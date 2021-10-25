#!/usr/bin/python3
from migen.fhdl.module import Module
from migen.fhdl.bitcontainer import *
from migen.fhdl.structure import Replicate
from migen import *
from migen.genlib.fsm import FSM, NextState, NextValue
from litex.soc.interconnect import stream

from cores.tf.testframe import testFrameDescriptor
from cores.tf.tfg import TestFrameGenerator

from litex.soc.interconnect.csr import *

"""
<-----   sys_clk   ---->|<---------------- phy_clk -------------------------->|<-----   sys_clk ----->
                +--- AsyncFIFO ---+     +-------- tfg ---------+     +--- AsyncFIFO ---+     
<sink_ctrl> --> |<sink>   <source>| --> |<sink_ctrl>   <source>| --> |<sink>   <source>| --> <source>
                +-----------------+     +----------------------+     +-----------------+     
"""
class DUT(Module):
    def __init__(self):
        
        cd_sys_name="sys"
        cd_phy_name="phy"
        
        # # #
        
        self.submodules.tfg = tfg = ClockDomainsRenamer(cd_phy_name)(TestFrameGenerator(data_width=32))
        self.submodules.cdc_s2p = cdc_s2p = stream.ClockDomainCrossing(
            tfg.sink_ctrl.description,
            cd_from=cd_sys_name,
            cd_to=cd_phy_name,
            depth=4)
        self.submodules.cdc_p2s = cdc_p2s = stream.ClockDomainCrossing(
            tfg.source.description,
            cd_from=cd_phy_name,
            cd_to=cd_sys_name,
            depth=16)
        
        self.comb += [
            cdc_s2p.source.connect(tfg.sink_ctrl),
            tfg.source.connect(cdc_p2s.sink)
        ]
        
        self.sink_ctrl = cdc_s2p.sink
        self.source = cdc_p2s.source
    
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
            yield

    def run_sim(self, **args):
        
        _generators = {
            "sys" : [
                self.tfg_test(),
                self.stream_handler(dut.source)
            ],
            "phy" : []
        }
        
        _clocks = {
            "sys" : 10,
            "phy" : 5,
        }
        
        run_simulation(self, clocks=_clocks, generators=_generators, **args)
                
if __name__ == "__main__":
    
    dut = DUT()
    dut.run_sim(vcd_name="tfg_oo.vcd")
    
