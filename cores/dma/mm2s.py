from migen import *
from litex.soc.interconnect.axi import AXIInterface, ax_description, r_description
from litex.soc.interconnect import stream, packet

from litepcie.common import request_layout, completion_layout
""" LitePCIe DMA Packet layout
def request_layout(data_width):
    layout = [
        ("we",               1), # Write:1 Read:0
        ("adr",             32), # Address
        ("len",             10), # Transfer length (DWORD)
        ("req_id",          16), # Requestor ID
        ("tag",              8), # Tag
        ("channel",          8), # For routing.
        ("user_id",          8)  # For packet identification.
        ("dat",     data_width), # Data beat
    ]
    return EndpointDescription(layout)

def completion_layout(data_width):
    layout = [
        ("adr",             32),
        ("len",             10),
        ("end",              1), # 分割が起こったときに最後のパケットを示す。分割されない場合は 1 で固定。
        ("req_id",          16),
        ("cmp_id",          16),
        ("err",              1),
        ("tag",              8),
        ("dat",     data_width),
        ("channel",          8), # For routing.
        ("user_id",          8)  # For packet identification.
    ]
    return EndpointDescription(layout)
"""

class DMARam(Module):
    def __init__(self, data_width, size):
        # Descriptor input
        self.sink = stream.Endpoint(request_layout(data_width))
        # Read data output
        self.source = stream.Endpoint(completion_layout(data_width))
        
        mem = Memory(data_width, size, init=range(size))
        self.specials += mem
        port = mem.get_port(write_capable=True)
        self.specials += port
        start_addr = Signal(len(self.sink.adr) - log2_int(data_width // 8), reset_less=True)
        offset = Signal(16, reset_less=True)
        
        self.comb += [
            self.source.end.eq(1)
        ]
                
        self.submodules.fsm = fsm = FSM(reset_state="Idle")
        fsm.act("Idle",
            If(self.sink.valid,
                # valid が有効な時点で有効なデータが到着しているため，ready を上げる前にヘッダを取り込む。
                NextValue(start_addr, self.sink.adr >> log2_int(data_width // 8)),
                NextValue(self.source.len, self.sink.len),
                NextValue(self.source.tag, self.sink.tag),
                NextValue(self.source.channel, self.sink.channel),
                NextValue(self.source.user_id, self.sink.user_id),
                NextValue(self.source.req_id, self.sink.req_id),
                NextValue(offset, 0),
                If(self.sink.we, NextState("WR")).Else(NextState("RD")),
            )
        )
        fsm.act("WR",
            self.sink.ready.eq(1),
            If(self.sink.valid,
                # Write data to memory
                port.we.eq(1),
                port.adr.eq(start_addr + offset),
                port.dat_w.eq(self.sink.dat),
                NextValue(offset, offset + 1),
                If (self.sink.last,
                    NextState("Idle")
                )
            ),
        )
        fsm.act("RD",
            self.sink.ready.eq(1),
            port.we.eq(0),
            port.adr.eq(start_addr + offset),
            NextState("RD2")
        )
        
        fsm.act("RD2",
            self.source.valid.eq(1),
            self.sink.ready.eq(0),
            port.we.eq(0),
            self.source.dat.eq(port.dat_r),
            If(((offset + 1 << log2_int(data_width//8)) >> 2) >= self.source.len,
                self.source.last.eq(1)
            ),
            If(self.source.ready,
                port.adr.eq(start_addr + offset + 1),
                NextValue(offset, offset + 1),
                If(self.source.last, 
                   NextValue(self.source.valid, 0), 
                   NextState("Idle")),
            ).Else(
                port.adr.eq(start_addr + offset)
            )
        )
        self.comb += [
            self.source.first.eq(offset == 0)
        ]

