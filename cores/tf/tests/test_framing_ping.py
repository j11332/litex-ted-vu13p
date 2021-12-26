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
            k2mm.source_packet_tx.connect(k2mm_peer.sink_packet_rx),
            k2mm_peer.source_packet_tx.connect(k2mm.sink_packet_rx)
        ]

    def put_request(self, len):
        ep = self.k2mm.sink_tester_ctrl
        yield ep.length.eq(len)
        yield ep.valid.eq(1)
        yield
        while (yield ep.ready) == 0:
            yield
        yield ep.valid.eq(0)
        yield
        for _ in range(len*2):
            yield
        
    def tfg_test(self):
        _test_frame_beats = [
            0, 1, 2, 10, 50, 100
        ]
        for l in _test_frame_beats:
            yield from self.put_request(l)
        yield

    @passive
    def print_latency(self):
        while True:
            yield self.k2mm.source_tester_status.ready.eq(1)
            if ((yield self.k2mm.source_tester_status.valid) & (yield self.k2mm.source_tester_status.ready)):
                print("Frame Length: {}, Latency: {} cycle[s]".format(
                        (yield self.k2mm.source_tester_status.length),
                        (yield self.k2mm.source_tester_status.latency),
                    )
                )
            # ［トラップ］一度制御を返さないと無限ループになる
            yield

    @passive
    def print_ping(self):
        while(True):
            if (yield self.k2mm.sink_tester_ctrl.valid) & (yield self.k2mm.sink_tester_ctrl.ready):
                print("ping:")
                print((yield from record_dump(self.k2mm.sink_tester_ctrl)))
            yield

    def run_sim(self, **args):
        
        _generators = {
            "sys" : [
                self.tfg_test(),
                self.print_latency(),
                self.print_ping()
            ],
        }
        
        _clocks = {
            "sys" : 10,
        }
        
        run_simulation(self, clocks=_clocks, generators=_generators, **args)

def record_dump(r: Record):
    dump = dict()
    for i in r.layout:
        if len(i) == 3:
            _sn, _w, _d = i
            _signal = getattr(r, _sn)
            dump[_sn] = (yield _signal)
        elif len(i) == 2:
            _rn, _layout = i
            _record = getattr(r, i[0])
            dump[_rn] = (yield from record_dump(_record))
        else:
            raise TypeError
    return dump

if __name__ == "__main__":    
    dut = _DUT(dw=32)
    dut.run_sim(vcd_name="framing_ping.vcd")
