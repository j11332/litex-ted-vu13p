#!/usr/bin/python3
from migen import *
from litex.soc.interconnect import stream
from cores.tf.packet import K2MMPacket

class TestFrameChecker(Module):
    def __init__(self, maxlen=65535, dw=256, error_counter_width=32):
        
        # Test frame (sink)
        self.sink = sink = stream.Endpoint(K2MMPacket.packet_user_description(dw=dw))
        self.source_tf_status = source_tf_status = stream.Endpoint(
            stream.EndpointDescription(
                [
                    ("err", 1),
                    ("length", log2_int(maxlen+1))
                ]
            )
        )
        # # #
        beats = Signal(max=maxlen, reset_less=True)
        data_matched = Signal()

        self.comb += [
            data_matched.eq(
                (sink.data == Replicate(beats, dw//len(beats))) & (sink.valid & sink.ready)),
            sink.ready.eq(1)
        ]

        _frame_err = Signal()
        
        # Counter
        self.sync += [
            If(sink.valid & sink.ready,
                If(sink.last,
                    beats.eq(0),
                    _frame_err.eq(0),
                    source_tf_status.valid.eq(1),
                    source_tf_status.err.eq(_frame_err),
                    source_tf_status.length.eq((beats + 1) * (dw//8)),
                ).Else(
                    source_tf_status.valid.eq(0),
                    beats.eq(beats + 1),
                    _frame_err.eq(_frame_err | ~data_matched)
                )
            ).Else(
                source_tf_status.valid.eq(0)
            )
        ]

