#!/usr/bin/python3
from migen import *
from litex.soc.interconnect.stream import EndpointDescription, Endpoint
from litex.soc.interconnect.packet import Packetizer, Header, HeaderField
from liteeth.common import eth_udp_user_description

def _remove_from_layout(layout, *args):
    r = []
    for f in layout:
        remove = False
        for arg in args:
            if f[0] == arg:
                remove = True
        if not remove:
            r.append(f)
    return r

class _Packet:
    magic                = 0x4e6f
    version              = 1
    header_length = 8
    header_fields = {
        "magic":     HeaderField(0, 0, 16),
        "version":   HeaderField(2, 4,  4),
        "nr":        HeaderField(2, 2,  1),
        "pr":        HeaderField(2, 1,  1),
        "pf":        HeaderField(2, 0,  1),
        "addr_size": HeaderField(3, 4,  4),
        "port_size": HeaderField(3, 0,  4)
    }
    header = Header(header_fields, header_length, swap_field_bytes=True)

    @staticmethod
    def packet_description(dw):
        param_layout = __class__.header.get_layout()
        payload_layout = [
            ("data",       dw),
            ("last_be", dw//8),
            ("error",   dw//8)
        ]
        return EndpointDescription(payload_layout, param_layout)
    
    @staticmethod
    def packet_user_description(dw):
        param_layout = __class__.header.get_layout()
        param_layout = _remove_from_layout(param_layout, "magic", "portsize", "addrsize", "version")
        param_layout += eth_udp_user_description(dw).param_layout
        payload_layout = [
            ("data",       dw),
            ("last_be", dw//8),
            ("error",   dw//8)
        ]
        return EndpointDescription(payload_layout, param_layout)

class K2MMPacketTX(Module):
            
    def __init__(self, udp_port=50000, dw=32):
    
        class K2MMPacketizer(Packetizer):
            def __init__(self, dw=32):
                super().__init__(
                    _Packet.packet_description(dw),
                    eth_udp_user_description(dw), 
                    _Packet.header)

        self.sink = sink = Endpoint(_Packet.packet_user_description(dw))
        self.source = source = Endpoint(eth_udp_user_description(dw))
        
        self.submodules.packetizer = packetizer = K2MMPacketizer(dw)
        self.comb += [
            sink.connect(packetizer.sink, omit={"src_port", "dst_port", "ip_address", "length"}),
            packetizer.sink.version.eq(_Packet.version),
            packetizer.sink.magic.eq(_Packet.magic),
            packetizer.sink.addr_size.eq(32 // 8),
            packetizer.sink.port_size.eq(32 // 8)
        ]
        
        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(packetizer.source.valid,
                NextState("SEND")
            )
        )
        fsm.act("SEND",
            packetizer.source.connect(source),
            source.src_port.eq(udp_port),
            source.dst_port.eq(udp_port),
            source.ip_address.eq(sink.ip_address),
            source.length.eq(sink.length + _Packet.header.length),
            If(source.valid & source.last & source.ready,
                NextState("IDLE")
            )
        )
        
        