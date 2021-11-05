#!/usr/bin/python3
from re import M
from cores.tf.packet import K2MMPacket
from cores.tf.tfg import TestFrameGenerator
from cores.tf.tfc import TestFrameChecker
from liteeth.common import eth_udp_user_description
from litex.soc.interconnect.packet import (Arbiter, Depacketizer, Dispatcher,
                                           Header, HeaderField, Packetizer)
from litex.soc.interconnect.stream import Endpoint, EndpointDescription, SyncFIFO
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
    def __init__(self, dw=32, bufferrized=True, fifo_depth=4):
        
        # TX/RX packet
        self.submodules.ptx = ptx = K2MMPacketTX(dw=dw)
        self.submodules.prx = prx = K2MMPacketRX(dw=dw)
        
        self.sink, self.source = ptx.sink, prx.source
        
        if bufferrized:
            tx_buffer = SyncFIFO(ptx.source.description, depth=fifo_depth)
            rx_buffer = SyncFIFO(prx.sink.description, depth=fifo_depth)
            self.submodules += [tx_buffer, rx_buffer]
            self.comb += [
                ptx.source.connect(tx_buffer.sink),
                rx_buffer.source.connect(prx.sink)
            ]
            self.source_packet_tx, self.sink_packet_rx = tx_buffer.source, rx_buffer.sink
        else:
            self.source_packet_tx = ptx.source
            self.sink_packet_rx = prx.sink

class _K2MMTester(Module):
    def __init__(self, dw=32, max_latency=65536):
        self.sink   = sink   = Endpoint(K2MMPacket.packet_user_description(dw))
        self.source = source = Endpoint(K2MMPacket.packet_user_description(dw))
        
        # # #

        self.submodules.tfg = tfg = TestFrameGenerator(data_width=dw)
        self.sink_ctrl = Endpoint(tfg.sink_ctrl.description)

        self.submodules.tfc = tfc = TestFrameChecker(dw=dw)
        self.comb += [
            sink.connect(tfc.sink),
            tfg.source.connect(source)
        ]

        self.latency = latency = Signal(max=max_latency)

        fsm = FSM(reset_state="STOP")
        fsm.act("STOP",
            self.sink_ctrl.connect(tfg.sink_ctrl),
            If(tfg.sink_ctrl.valid & tfg.sink_ctrl.ready,
                NextState("COUNT_LATENCY"),
                NextValue(latency, 0),
            ),
        )

        fsm.act("COUNT_LATENCY",
            NextValue(latency, latency + 1),
            tfc.source_tf_status.ready.eq(1),
            If(tfc.source_tf_status.valid == 1,
                NextState("STOP")
            ),
        )
        self.submodules += fsm
        self.source_status = Endpoint(
            EndpointDescription(
                tfc.source_tf_status.description.payload_layout + 
                    [("latency", latency.nbits)],
                tfc.source_tf_status.description.param_layout)
        )
        self.comb += [
            tfc.source_tf_status.connect(self.source_status, omit={"latency"}),
            self.source_status.latency.eq(latency),
            self.source_status.ready.eq(1)
        ]
        
from litex.soc.interconnect.stream import Endpoint, DIR_SOURCE, DIR_SINK
from util.axi import EP2AXI

class K2MM(Module):
    def __init__(self, dw=32):
        # Packet parser
        self.submodules.packet = packet = _K2MMPacketParser(dw=dw)
        self.source_packet_tx = Endpoint(packet.source_packet_tx.description, name="pkt_tx")
        self.sink_packet_rx = Endpoint(packet.sink_packet_rx.description, name="pkt_rx")
        self.comb += [
            packet.source_packet_tx.connect(self.source_packet_tx),
            self.sink_packet_rx.connect(packet.sink_packet_rx)
        ]
        # function modules
        self.submodules.probe = probe = K2MMProbe(dw=dw)
        self.submodules.tester = tester = _K2MMTester(dw=dw)
        self.source_tester_status = tester.source_status
        self.sink_tester_ctrl = tester.sink_ctrl

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

if __name__ == "__main__":
    from migen.fhdl.verilog import convert
    k2mm = K2MM()
    _axi_map = {
        "source_packet_tx"      : DIR_SOURCE,
        "sink_packet_rx"        : DIR_SINK,
    }
    
    k2mm = EP2AXI(_axi_map)(k2mm)
    _ios = k2mm.ios
    _ios += k2mm.sink_tester_ctrl.payload.flatten()
    _ios += [k2mm.sink_tester_ctrl.valid, k2mm.sink_tester_ctrl.ready]
    _ios += k2mm.source_tester_status.payload.flatten()
    _ios += [k2mm.source_tester_status.valid, k2mm.source_tester_status.ready]
    
    convert(k2mm, ios=set(_ios)).write("K2MM.v")