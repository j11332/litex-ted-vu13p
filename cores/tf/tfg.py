#!/usr/bin/python3
from migen.fhdl.module import Module
from migen.fhdl.bitcontainer import *
from migen.fhdl.structure import Replicate
from migen import *
from migen.genlib.fsm import FSM, NextState, NextValue
from litex.soc.interconnect import stream

from testframe import testFrameDescriptor
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
            testFrameDescriptor(data_width),
            name="tf_src")

        # # #

        beats = Signal(max=maxlen, reset_less=True)
        length = Signal.like(sink_ctrl.length)

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
            source.valid.eq(1),
            source.last.eq(beats == length),
            If(source.ready == 1,
                If(beats == length,
                    NextState("DONE"),
                ).Else(
                    NextValue(beats, beats + 1)
                )
            )
        )
        fsm.act("DONE",
            sink_ctrl.ready.eq(0),
            source.valid.eq(0),
            NextState("IDLE")
        )
        self.submodules += fsm

def _tfg_driver(ep):
    def put_request(len):
        yield ep.length.eq(len)
        yield ep.valid.eq(1)
        yield
        while (yield ep.ready) == 0:
            yield
        yield ep.valid.eq(0)
        yield

    yield from put_request(1)
    yield from put_request(2)
    yield from put_request(10)

def tfg_test(dut):
    yield dut.source.ready.eq(1)
    yield from _tfg_driver(dut.sink_ctrl)
    while (yield dut.source.last) == 0:
        yield
    yield
"""

<-----   sys_clk   ---->|<---------------- phy_clk ------------------------>|
                +--- AsyncFIFO ---+     +-------- tfg ---------+
<sink_ctrl> --> |<sink>   <source>| --> |<sink_ctrl>   <source>| --> <source>
                +-----------------+     +----------------------+
"""
class DUT(Module):
    def __init__(self):
        self.sink_ctrl = sink_ctrl = stream.Endpoint(
            TestFrameGenerator.getControlInterfaceDescriptor()
        )
        self.submodules.tfg = tfg = ClockDomainsRenamer("phy")(TestFrameGenerator())
        self.source = tfg.source

        # # #

        _ctrl_buf = stream.AsyncFIFO(TestFrameGenerator.getControlInterfaceDescriptor())
        _ctrl_buf = ClockDomainsRenamer({"write" : "sys", "read" : "phy"})(_ctrl_buf)
        self.comb += sink_ctrl.connect(_ctrl_buf.sink)
        self.comb += _ctrl_buf.source.connect(tfg.sink_ctrl)
        self.submodules += _ctrl_buf

if __name__ == "__main__":
    _clocks = {
        "sys" : 10,
        "phy" : 5,
    }
    dut = DUT()
    run_simulation(dut, tfg_test(dut), clocks = _clocks, vcd_name = "tfg.vcd")
