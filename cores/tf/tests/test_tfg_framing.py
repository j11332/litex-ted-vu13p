#!/usr/bin/python3
from migen.fhdl.module import Module
from migen.fhdl.bitcontainer import *
from migen.fhdl.structure import Replicate
from migen import *
from migen.genlib.fsm import FSM, NextState, NextValue
from litex.soc.interconnect import stream

from cores.tf.testframe import testFrameDescriptor
from cores.tf.tfg import TestFrameGenerator
from cores.tf.framing import K2MMPacketTX

from litex.soc.interconnect.csr import *

class _DUT(Module):
    def __init__(self, dw=32):
        
        cd_sys_name="sys"
               
        # # #
        
        self.submodules.tfg = tfg = TestFrameGenerator(data_width=dw)
        self.submodules.tx_framing = tx_framing = K2MMPacketTX(dw=dw)
        
        self.comb += tfg.source.connect(tx_framing.sink)
        
        self.sink_ctrl = tfg.sink_ctrl
        self.source = tx_framing.source
    
    def tfg_test(self):
        
        def _tfg_driver(dut):
            ep = dut.sink_ctrl
            def put_request(len):
                yield ep.length.eq(len)
                yield ep.valid.eq(1)
                yield
                while (yield ep.ready) == 0:
                    yield
                yield ep.valid.eq(0)
                
                while ((yield dut.source.last) == 0):
                    yield
                yield
            
            yield from put_request(0)    
            yield from put_request(1)
            yield from put_request(2)
            yield from put_request(10)

        yield self.source.ready.eq(1)
        yield from _tfg_driver(self)

    @staticmethod
    @passive
    def stream_handler(ep):
        while True:
            if (yield ep.valid) and (yield ep.ready):
                print('0x{:08x} first={}, last={}, len={}'.format((yield ep.data), (yield ep.first), (yield ep.last), (yield ep.length)))
                for key, _, __ in ep.param.layout:
                    print("{}={:x}".format(key, (yield getattr(ep, key))))
            yield

    def run_sim(self, **args):
        
        _generators = {
            "sys" : [
                self.tfg_test(),
                self.stream_handler(dut.source)
            ],
        }
        
        _clocks = {
            "sys" : 10,
        }
        
        run_simulation(self, clocks=_clocks, generators=_generators, **args)
                
if __name__ == "__main__":
    
    dut = _DUT()
    dut.run_sim(vcd_name="tfg_oo.vcd")
    
