from liteeth.common import eth_udp_user_description
from litex.soc.interconnect.packet import (Arbiter, Depacketizer, Dispatcher,
                                           Header, HeaderField, Packetizer)
from litex.soc.interconnect.stream import Endpoint, EndpointDescription
from migen import *

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

class K2MMPacket:
    magic                = 0x4f6f
    version              = 1
    header_length = 8
    header_fields = {
        "magic":     HeaderField(0, 0, 16),
        "version":   HeaderField(2, 4,  4),
        "nr":        HeaderField(2, 2,  1),
        "pr":        HeaderField(2, 1,  1),
        "pf":        HeaderField(2, 0,  1),
        "addr_size": HeaderField(3, 0,  8),
        "port_size": HeaderField(4, 0,  8)
    }
    header = Header(header_fields, header_length, swap_field_bytes=True)

    @staticmethod
    def get_header(dw, aligned=True):
        return Header(
            __class__.header_fields,
            length = dw // 8 if aligned else __class__.header_length,
            swap_field_bytes = True)
    
    @staticmethod
    def packet_description(dw):
        param_layout = __class__.get_header(dw).get_layout()
        payload_layout = [
            ("data",       dw),
            ("last_be", dw//8),
            ("error",   dw//8)
        ]
        return EndpointDescription(payload_layout, param_layout)
    
    @staticmethod
    def packet_user_description(dw):
        param_layout = __class__.get_header(dw).get_layout()
        param_layout = _remove_from_layout(param_layout, "magic", "portsize", "addrsize", "version")
        param_layout += eth_udp_user_description(dw).param_layout
        payload_layout = [
            ("data",       dw),
            ("last_be", dw//8),
            ("error",   dw//8)
        ]
        return EndpointDescription(payload_layout, param_layout)
