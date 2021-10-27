#!/usr/bin/python3
from migen.fhdl.module import Module
from migen.fhdl.bitcontainer import *
from migen.fhdl.structure import Replicate
from migen import *
from migen.genlib.fsm import FSM, NextState, NextValue
from litex.soc.interconnect import stream

from cores.tf.testframe import testFrameDescriptor
from cores.tf.tfg import TestFrameGenerator
from cores.tf.tfc import TestFrameChecker
from cores.tf.framing import *

from litex.soc.interconnect.csr import *

class _DUT(Module):
    def __init__(self, dw=32):
        
        # # #
        
        self.submodules.tfg  = tfg  = TestFrameGenerator(data_width=dw)
        self.submodules.fifo = fifo = stream.SyncFIFO(tfg.source.description, 16)
        self.submodules.tfc  = checker  = TestFrameChecker(dw=dw)
        self.comb += [
            tfg.source.connect(fifo.sink),
            fifo.source.connect(checker.sink),
        ]

    def _tfg_put_request(self, len):

        yield self.tfg.sink_ctrl.length.eq(len)
        yield self.tfg.sink_ctrl.valid.eq(1)
        yield
        while (yield self.tfg.sink_ctrl.ready) == 0:
            yield
        yield self.tfg.sink_ctrl.valid.eq(0)
        
        while ((yield self.tfg.source.last) == 0):
            yield
        yield

    def tfg_test(self):
        yield from self._tfg_put_request(0)
        yield from self._tfg_put_request(1)
        yield from self._tfg_put_request(2)
        yield from self._tfg_put_request(10)
        yield
        
    @passive
    def stream_handler(self):
        ep = self.tfg.source
        while True:
            if (yield ep.valid) and (yield ep.ready):
                print('0x{:x} first={}, last={}, len={}'.format((yield ep.data), (yield ep.first), (yield ep.last), (yield ep.length)))
                # for key, _, __ in ep.param.layout:
                #     print("{}={:x}".format(key, (yield getattr(ep, key))))
            yield

    def run_sim(self, **args):
        
        _generators = {
            "sys" : [
                self.tfg_test(),
                self.stream_handler()
            ],
        }
        
        _clocks = {
            "sys" : 10,
        }
        
        run_simulation(self, clocks=_clocks, generators=_generators, **args)
                
if __name__ == "__main__":
    dut = _DUT(dw=32)
    dut.run_sim(vcd_name="tfc.vcd")