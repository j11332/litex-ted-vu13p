#!/usr/bin/python3
from migen.fhdl.module import Module
from migen.fhdl.bitcontainer import *
from migen.fhdl.structure import Replicate
from migen import *
from cores.tf.framing import K2MM

from litex.soc.interconnect.csr import *

class _DUT(Module):
    def __init__(self, dw=32):
        self.submodules.k2mm = k2mm = K2MM(dw=dw)
        self.submodules.k2mm_peer = k2mm_peer = K2MM(dw=dw)
        self.comb += [
            k2mm.packet.source_packet_tx.connect(k2mm_peer.packet.sink_packet_rx),
            k2mm_peer.packet.source_packet_tx.connect(k2mm.packet.sink_packet_rx)
        ]

    def put_request(self, len):
        ep = self.k2mm.tester.tfg.sink_ctrl
        yield ep.length.eq(len)
        yield ep.valid.eq(1)
        yield
        while (yield ep.ready) == 0:
            yield
        yield ep.valid.eq(0)
        
        while ((yield self.k2mm.tester.tfg.source.last) == 0):
            yield
        yield

    def tfg_test(self):
        yield from self.put_request(0)    
        yield from self.put_request(1)
        yield from self.put_request(2)
        yield from self.put_request(10)
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
    
    dut = _DUT(dw=32)
    dut.run_sim(vcd_name="framing_ping.vcd")
