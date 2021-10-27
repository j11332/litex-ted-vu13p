#!/usr/bin/python3
from cores.tf.packet import K2MMPacket
from cores.tf.tfg import TestFrameGenerator
from cores.tf.tfc import TestFrameChecker
from liteeth.common import eth_udp_user_description
from litex.soc.interconnect.packet import (Arbiter, Depacketizer, Dispatcher,
                                           Header, HeaderField, Packetizer)
from litex.soc.interconnect.stream import Endpoint, EndpointDescription
from migen import *

class K2MMPacketTX(Module):
            
    def __init__(self, udp_port=50000, dw=32):
    
        class K2MMPacketizer(Packetizer):
            def __init__(self, dw=32):
                super().__init__(
                    K2MMPacket.packet_description(dw),
                    eth_udp_user_description(dw), 
                    K2MMPacket.get_header(dw))

        self.sink = sink = Endpoint(K2MMPacket.packet_user_description(dw))
        self.source = source = Endpoint(eth_udp_user_description(dw))
        
        self.submodules.packetizer = packetizer = Packetizer(
            K2MMPacket.packet_description(dw),
            source.description,
            K2MMPacket.get_header(dw)
        )
        self.comb += [
            sink.connect(packetizer.sink, omit={"src_port", "dst_port", "ip_address", "length"}),
            packetizer.sink.version.eq(K2MMPacket.version),
            packetizer.sink.magic.eq(K2MMPacket.magic),
            packetizer.sink.addr_size.eq(dw // 8),
            packetizer.sink.port_size.eq(dw // 8)
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
            source.length.eq(sink.length + K2MMPacket.get_header(dw).length),
            If(source.valid & source.last & source.ready,
                NextState("IDLE")
            )
        )

class K2MMPacketRX(Module):
    def __init__(self, dw=32):
        self.sink = sink = Endpoint(eth_udp_user_description(dw))
        self.source = source = Endpoint(K2MMPacket.packet_user_description(dw))

        # # #
        
        self.submodules.dpkt0 = depacketizer = Depacketizer(
            sink.description,
            K2MMPacket.packet_description(dw),
            K2MMPacket.get_header(dw)
        )
        self.comb += self.sink.connect(depacketizer.sink)

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(depacketizer.source.valid,
                NextState("DROP"),
                If(depacketizer.source.magic == K2MMPacket.magic,
                    NextState("RECEIVE")
                )
            )
        )
        self.comb += [
            # FIXME: flag for "user" header fields
            depacketizer.source.connect(source, keep={"last", "pf", "pr", "nr", "data"}),
            source.src_port.eq(sink.src_port),
            source.dst_port.eq(sink.dst_port),
            source.ip_address.eq(sink.ip_address),
            source.length.eq(sink.length - K2MMPacket.get_header(dw).length)
        ]
        fsm.act("RECEIVE",
            depacketizer.source.connect(source, keep={"valid", "ready"}),
            If(source.valid & source.ready,
                If(source.last,
                    NextState("IDLE")
                )
            )
        )
        fsm.act("DROP",
            depacketizer.source.ready.eq(1),
            If(depacketizer.source.valid &
                depacketizer.source.last &
                depacketizer.source.ready,
                NextState("IDLE")
            )
        )

class K2MMProbe(Module):
    def __init__(self, dw=32):
        self.sink   = sink   = Endpoint(K2MMPacket.packet_user_description(dw))
        self.source = source = Endpoint(K2MMPacket.packet_user_description(dw))

        # # #

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(sink.valid,
                NextState("PROBE_RESPONSE")
            )
        )
        fsm.act("PROBE_RESPONSE",
            sink.connect(source),
            source.pf.eq(0),
            source.pr.eq(1),
            If(source.valid & source.ready,
                If(source.last,
                    NextState("IDLE")
                )
            )
        )
       
class _K2MMPacketParser(Module):
    def __init__(self, dw=32):
        
        # TX/RX packet
        self.submodules.ptx = ptx = K2MMPacketTX(dw=dw)
        self.submodules.prx = prx = K2MMPacketRX(dw=dw)
        
        self.sink, self.source = self.ptx.sink, self.prx.source

class _K2MMTester(Module):
    def __init__(self, dw=32):
        self.sink   = sink   = Endpoint(K2MMPacket.packet_user_description(dw))
        self.source = source = Endpoint(K2MMPacket.packet_user_description(dw))
        
        # # #

        self.submodules.tfg = tfg = TestFrameGenerator(data_width=dw)
        self.submodules.tfc = tfc = TestFrameChecker(dw=dw)
        self.comb += [
            sink.connect(tfc.sink),
            tfg.source.connect(source)
        ]

class K2MM(Module):
    def __init__(self, dw=32):
        # Packet parser
        self.submodules.packet = packet = _K2MMPacketParser(dw=dw)

        # function modules
        self.submodules.probe = probe = K2MMProbe(dw=dw)
        self.submodules.tester = tester = _K2MMTester(dw=dw)
        
        # Arbitrate source endpoints
        self.submodules.arbiter = arbiter = Arbiter(
            [
                probe.source,
                tester.source,
            ],
            packet.sink
        )
 
        # Dispatcher
        self.submodules.dispatcher = dispatcher = Dispatcher(
            packet.source,
            [
                tester.sink,
                probe.sink
            ]
        )
        self.comb += [dispatcher.sel.eq(packet.source.pf)]
                