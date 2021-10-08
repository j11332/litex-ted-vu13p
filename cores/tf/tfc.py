#!/usr/bin/python3
from migen import *
from litex.soc.interconnect import stream
from testframe import testFrameDescriptor

class TestFrameChecker(Module):
    class Buffered(Module):
        def __init__(self, data :Signal):
            self.buf = buf = Signal().like(data)
            self.sync += [buf.eq(data)]

    def __init__(self, maxlen=65536, data_width=256, error_counter_width=32):
        self.timer_stop = Signal()
        self.err_count = Signal(error_counter_width)
        self.err_count_reset = Signal()
        self.data_matched = data_matched = Signal()
        self.frame_valid = frame_valid = Signal()
        self.sink = stream.Endpoint(testFrameDescriptor(data_width))

        # # #
        databuf = self.Buffered(self.sink.data)
        beats = Signal(max=maxlen, reset_less=True)
        self.comb += [data_matched.eq(databuf.buf == Replicate(beats, data_width//len(beats)))]
        _frame_err = Signal()
        fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            self.sink.ready.eq(1),
            If(self.sink.valid,
                NextValue(beats, 0),
                NextValue(_frame_err, _frame_err & (~data_matched)),
                If(self.sink.last,
                    NextState("LAST")
                ).Else(
                    NextState("RUN"),
                )
            )
        )
        fsm.act("RUN",
            self.sink.ready.eq(1),
            If(self.sink.valid,
                NextValue(beats, beats + 1),
                NextValue(_frame_err, _frame_err & (~data_matched)),
                If(self.sink.last, NextState("LAST"))
            )
        )
        fsm.act("LAST",
            self.timer_stop.eq(1),
            self.frame_valid.eq(~_frame_err),
            self.sink.ready.eq(0),
            NextValue(beats, 0),
            NextState("IDLE")
        )
        self.submodules.fsm = fsm
        self.submodules += databuf
