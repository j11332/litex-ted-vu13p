#!/usr/bin/python3
from migen.fhdl.module import Module
from migen.fhdl.bitcontainer import *
from migen.fhdl.structure import Replicate
from migen import *
from cores.kyokko.aurora import _ResetSequencer
class DUT(Module):
    def __init__(self):
        self.reset = Signal()
        self.reset2 = Signal()
        self.submodules.rgen = rgen = _ResetSequencer(pma_wait=5, reset_width=10)
        rgen.add_reset(self.reset, edge=True)
        rgen.add_reset(self.reset2, edge=True)

    def tfg_test(self):
        yield self.reset.eq(0)
        yield
        yield self.reset.eq(1)
        yield
        yield
        yield
        yield
        while (yield self.rgen.reset_pb) != 0:
            yield
        yield
        yield
        yield self.reset2.eq(0)
        yield
        yield self.reset2.eq(1)
        yield
        yield
        yield
        yield
        while (yield self.rgen.reset_pb) != 0:
            yield
        yield

    def run_sim(self, **args):
        
        _generators = {
            "sys" : [
                self.tfg_test(),
            ],
        }
        
        _clocks = {
            "sys" : 10,
        }
        
        run_simulation(self, clocks=_clocks, generators=_generators, **args)
                
if __name__ == "__main__":
    
    dut = DUT()
    dut.run_sim(vcd_name="rg_test.vcd")
    
