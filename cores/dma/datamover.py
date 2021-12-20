from migen import *
from litex.soc.interconnect import stream

class S2MMRequestEndpoint(stream.Endpoint):
    def __init__(self, dw, aw, maxlen, tag = None, name = None):
        _payload = [
            ("data", dw)
        ]
        _param = [
            ("adr", aw),
            ("len", bits_for(maxlen)),
        ]
        
        if tag is not None:
            _param += [tag]
        
        stream.Endpoint.__init__(
            self, stream.EndpointDescription(_payload, _param), name=name)

class S2MMCompleteEndpoint(stream.Endpoint):
    def __init__(self, tag = None, name = None):
        
        _payload = [
            ("status", 1),
        ]
        
        if tag is not None:
            _payload += [tag]
        
        stream.Endpoint.__init__(
            self, 
            stream.EndpointDescription(_payload),
            name = name
        )

from litex.soc.interconnect.axi import AXIInterface, BURST_INCR, RESP_OKAY, RESP_DECERR, RESP_SLVERR
from typing import Optional, Union
class DataMoverS2MM(Module):
    def __init__(self, maxlen : int,
            dw : Optional[int], 
            aw : Optional[int],
            axi : Optional[AXIInterface],
            tag : Union[stream.EndpointDescription, Record, None]):    
        
        self.sink_ctrl = sink_ctrl = S2MMRequestEndpoint(
            dw if axi is None else axi.data_width,
            aw if axi is None else axi.address_width,
            maxlen = 4096, # AXI の仕様上の上限
            tag=tag
        )
        # AXI MM Master
        self.axi = AXIInterface(dw, aw) if axi is None else axi
        # Write request port
        self.source_status = S2MMCompleteEndpoint(tag=tag)
        # IRQ
        # self.irq = Signal(reset = None)
        
        # # #
        
        self.comb += [
            self.axi.aw.addr.eq(sink_ctrl.adr),
            self.axi.aw.burst.eq(BURST_INCR),
            self.axi.aw.lock.eq(0),
            self.axi.aw.cache.eq(0b0001),
            self.axi.aw.prot.eq(0b0),
            self.axi.aw.size.eq(bits_for(self.axi.data_width // 8) - 1),
            self.axi.aw.len.eq(sink_ctrl.len >> bits_for(self.axi.data_width // 8) - 1),
        ]
        
        self.comb += [
            self.axi.w.strb.eq(Replicate(0b1, len(self.axi.w.strb)))
        ]
        
        _data_buf = stream.Endpoint(self.axi.w.description)
        self.submodules.fsm = fsm = FSM(reset_state="Idle")
        fsm.act("Idle",
            sink_ctrl.ready.eq(self.axi.aw.ready),
            self.axi.aw.valid.eq(sink_ctrl.valid),
            self.axi.w.data.eq(sink_ctrl.data),
            self.axi.w.last.eq(sink_ctrl.last),
            self.axi.w.valid.eq(sink_ctrl.valid),
            If(sink_ctrl.valid,
                If (self.axi.aw.ready & self.axi.w.ready,
                    NextState("SendPayload")
                ).Elif(self.axi.aw.ready & ~self.axi.w.ready,
                    NextValue(_data_buf.last, sink_ctrl.last),
                    NextValue(_data_buf.data, sink_ctrl.data),
                    NextState("DataReadyWait")
                )
            )
        )
        fsm.act("DataReadyWait",
            sink_ctrl.ready.eq(0),
            self.axi.w.connect(_data_buf, omit={"ready", "valid", "strb"}),
            self.axi.w.valid.eq(1),
            If(self.axi.w.ready & self.axi.w.valid,
                NextState("SendPayload")
            )
        )
        fsm.act("SendPayload", 
            sink_ctrl.ready.eq(self.axi.w.ready),
            self.axi.w.valid.eq(sink_ctrl.valid),
            self.axi.w.data.eq(sink_ctrl.data),
            self.axi.w.last.eq(sink_ctrl.last),
            If(self.axi.w.ready & self.axi.w.valid & self.axi.w.last,
                NextState("Idle")
            )
        )
    
class _DUT(Module):
    def __init__(self):
        self.submodules.dma = dma = DataMoverS2MM(4096, 32, 32, axi=None, tag=None)
        self.s_axi = dma.axi
        
    # for simulation
    @staticmethod
    def put_request(port, addr, count):
        for beat in range(count):
            yield port.adr.eq(addr)
            yield port.len.eq(count * (len(port.data) // 8))
            yield port.data.eq(beat)
            yield port.last.eq(1 if beat == (count - 1) else 0)
            yield port.first.eq(1 if beat == 0 else 0)
            yield port.valid.eq(1)
            while (yield port.ready) == 0:
                yield
            yield
        
        yield port.valid.eq(0)
    
    def sim_control(self):
        yield self.dma.axi.aw.ready.eq(1)
        yield self.dma.axi.w.ready.eq(1)
        yield
        yield from self.put_request(self.dma.sink_ctrl, 0x100, 16)
        yield
        
    def run_sim(self, **args):
        
        _generators = {
            "sys" : [
                self.sim_control()
            ],
        }
        
        _clocks = {
            "sys" : 10,
        }
        
        run_simulation(self, clocks=_clocks, generators=_generators, **args)

if __name__ == "__main__":
    dut = _DUT()
    dut.run_sim(vcd_name="dma.vcd")