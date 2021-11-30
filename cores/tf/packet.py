from liteeth.common import eth_udp_user_description
from litex.soc.interconnect.packet import (Arbiter, Depacketizer, Dispatcher,
                                           Header, HeaderField, Packetizer)
from litex.soc.interconnect.stream import Endpoint, EndpointDescription
from migen import *

class _HeaderField(HeaderField):
    def __init__(self, byte, offset, width, user = True):
        super().__init__(byte, offset, width)
        self.user = user

class _Header(Header):
    def __init__(self, fields, length, swap_field_bytes=True):
        super().__init__(fields, length, swap_field_bytes=True)
    
    def get_user_layout(self):
        layout = []
        for k, v in filter(lambda x: x[1].user == True, self.fields.items()):
            layout.append((k, v.width))
        return layout

class K2MMPacket:
    magic                = 0x4f6f
    version              = 1
    header_length = 8
    header_fields = {
        "magic":     _HeaderField(0, 0, 16, user=False),
        "version":   _HeaderField(2, 4,  4, user=False),
        "nr":        _HeaderField(2, 2,  1, user=True),
        "pr":        _HeaderField(2, 1,  1, user=True),
        "pf":        _HeaderField(2, 0,  1, user=True),
        "addr_size": _HeaderField(3, 0,  8, user=False),
        "port_size": _HeaderField(4, 0,  8, user=False)
    }
    header = Header(header_fields, header_length, swap_field_bytes=True)

    @staticmethod
    def get_header(dw, aligned=True):
        return _Header(
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
        param_layout = __class__.get_header(dw).get_user_layout()
        # param_layout = _remove_from_layout(param_layout, "magic", "portsize", "addrsize", "version")
        param_layout += eth_udp_user_description(dw).param_layout
        payload_layout = [
            ("data",       dw),
            ("last_be", dw//8),
            ("error",   dw//8)
        ]
        return EndpointDescription(payload_layout, param_layout)

