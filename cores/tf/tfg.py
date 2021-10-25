#!/usr/bin/python3
from migen.fhdl.module import Module
from migen.fhdl.bitcontainer import *
from migen.fhdl.structure import Replicate
from migen import *
from migen.genlib.fsm import FSM, NextState, NextValue
from litex.soc.interconnect import stream

from cores.tf.testframe import testFrameDescriptor
from cores.tf.framing import K2MMPacket
from litex.soc.interconnect.csr import *

class TFGController(Module, AutoCSR):
    def __init__(self, tfg):
        self.submodules.tfg = tfg
        self.tfg_control = tfg_control = CSRStorage(
            fields=[
                CSRField("start", size=1),
                CSRField("length", size=len(tfg.length), 
                    description="Length of test frame."
                )
            ]
        )
        self.tfg_status = tfg_status = CSRStatus(
            fields=[
                CSRField("busy", size=1, values=[
                    ("``0b0``", "Idle"),
                    ("``0b1``", "Busy"),
                ]),
            ]
        )

        self.comb += [
            tfg.start.eq(tfg_control.fields.start),
            tfg.length.eq(tfg_control.fields.length),
            tfg_status.fields.busy.eq(tfg.busy),
        ]

class TestFrameGenerator(Module):
    @staticmethod
    def getControlInterfaceDescriptor(maxlen=65536):
        return stream.EndpointDescription(
            [("length", log2_int(maxlen))]
        )

    def __init__(self, maxlen=65536, data_width=256):
        self.sink_ctrl = sink_ctrl = stream.Endpoint(
            self.getControlInterfaceDescriptor(maxlen=maxlen)
        )
        self.source = source = stream.Endpoint(
            K2MMPacket.packet_user_description(dw=data_width))

        # # #

        beats = Signal(max=maxlen, reset_less=True)
        length = Signal.like(sink_ctrl.length)
        
        # Status Signal
        self.busy = busy = Signal()
        self.sync += busy.eq(sink_ctrl.valid | (sink_ctrl.ready == 0))
        
        fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            sink_ctrl.ready.eq(1),
            If(sink_ctrl.valid,
                NextState("RUN"),
                NextValue(length, sink_ctrl.length),
                NextValue(beats, 0),
            )
        )
        fsm.act("RUN",
            sink_ctrl.ready.eq(0),
            source.data.eq(Replicate(beats, data_width//len(beats))),
            source.length.eq((length + 1) * (data_width//8)),
            source.valid.eq(1),
            source.first.eq(beats == 0),
            If(source.ready == 1,
                If(beats == length,
                    NextState("IDLE"),
                ).Else(
                    NextValue(beats, beats + 1)
                )
            ),
            If(beats == length,
                source.last.eq(1),
                source.last_be.eq(Replicate(C(1), data_width//8)),
            ).Else(
                source.last.eq(0),
                source.last_be.eq(0),
            ),
        )
        # fsm.act("DONE",
        #     sink_ctrl.ready.eq(0),
        #     source.valid.eq(0),
        #     NextState("IDLE")
        # )
        self.submodules += fsm

