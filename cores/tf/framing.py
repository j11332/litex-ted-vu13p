#!/usr/bin/python3
from re import M

from migen import *
from litex.soc.interconnect.csr import CSRStatus
from liteeth.common import eth_udp_user_description
from litex.soc.interconnect.packet import Arbiter, Depacketizer, Dispatcher, Packetizer
from litex.soc.interconnect.stream import Endpoint, EndpointDescription, SyncFIFO

from cores.tf.packet import K2MMPacket
from cores.tf.tfg import TestFrameGenerator
from cores.tf.tfc import TestFrameChecker
from util.epbuf import SkidBufferInsert

class K2MMPacketTX(Module):
    def __init__(self, udp_port=50000, dw=32):
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
            packetizer.sink.addr_size.eq(64),
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
    def __init__(self, dw=32, bufferrized=True, fifo_depth=256):
        
        # TX/RX packet
        ptx = K2MMPacketTX(dw=dw)
        ptx = SkidBufferInsert({"sink": DIR_SINK})(ptx)
        self.submodules.ptx = ptx

        prx = K2MMPacketRX(dw=dw)
        prx = SkidBufferInsert({"source": DIR_SOURCE})(prx)
        self.submodules.prx = prx
        
        self.sink, self.source = ptx.sink, prx.source
        from cores.xpm_fifo import XPMStreamFIFO
        if bufferrized:
            self.submodules.tx_buffer = tx_buffer = SyncFIFO(ptx.source.description, depth=fifo_depth, buffered=True)
            self.submodules.rx_buffer = rx_buffer = SyncFIFO(prx.sink.description, depth=fifo_depth, buffered=True)
            self.comb += [
                ptx.source.connect(tx_buffer.sink),
                rx_buffer.source.connect(prx.sink)
            ]
            self.source_packet_tx = Endpoint(tx_buffer.source.description)
            self.sink_packet_rx = Endpoint(rx_buffer.sink.description)
            self.comb += [
                self.sink_packet_rx.connect(rx_buffer.sink),
                tx_buffer.source.connect(self.source_packet_tx)
            ]
        else:
            self.source_packet_tx = ptx.source
            self.sink_packet_rx = prx.sink

class K2MMTester(Module):
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
class K2MM(Module):
    def __init__(self, dw=32, cd="sys"):
        
        # Packet parser
        self.submodules.packet = packet = _K2MMPacketParser(dw=dw)
        self.source_packet_tx = Endpoint(packet.source_packet_tx.description, name="source_packet_tx")
        self.sink_packet_rx = Endpoint(packet.sink_packet_rx.description, name="sink_packet_rx")
        self.comb += [
            packet.source_packet_tx.connect(self.source_packet_tx),
            self.sink_packet_rx.connect(packet.sink_packet_rx)
        ]

        # function modules
        self.submodules.probe = probe = K2MMProbe(dw=dw)
        self.submodules.tester = tester = K2MMTester(dw=dw)
        self.source_tester_status = Endpoint(tester.source_status.description)
        self.sink_tester_ctrl = Endpoint(tester.sink_ctrl.description)
        self.comb += [
            tester.source_status.connect(self.source_tester_status),
            self.sink_tester_ctrl.connect(tester.sink_ctrl)
        ]
        self.submodules.record = record = K2MMRecord(dw)
        
        # Arbitrate source endpoints
        self.submodules.arbiter = arbiter = Arbiter(
            [
                record.source,
                probe.source,
                tester.source,
            ],
            packet.sink
        )
 
        # Dispatcher                        
        """ 
                                        disp_test
                                         +---+
                                         |   |---> tester
             disp_probe              +-->|   |                   
                +---+                |   |   |---> probe        
                |   |--probe_stream--+   +---+
        RX  --->|   |     
                |   |---------------> record
                +---+
        """
        probe_stream = Endpoint(K2MMPacket.packet_user_description(dw))
        self.submodules.disp_probe = disp_probe = Dispatcher(
            packet.source, [record.sink, probe_stream])
        self.comb += disp_probe.sel.eq(packet.source.pf | packet.source.pr)
        
        self.submodules.disp_test = disp_test = Dispatcher(
            probe_stream, [tester.sink, probe.sink])
        self.comb += disp_test.sel.eq(probe_stream.pf)

    def get_ios(self):
        return [
            self.source_packet_tx,
            self.sink_packet_rx,
            self.source_tester_status,
            self.sink_tester_ctrl,
        ]

class K2MMRecord(Module):
    def __init__(self, dw):
        self.sink = sink = Endpoint(K2MMPacket.packet_user_description(dw))
        self.source = source = Endpoint(K2MMPacket.packet_user_description(dw))
        
from litex.soc.interconnect.csr_eventmanager import AutoCSR, CSRStatus, CSRStorage, CSRField
class K2MMControl(Module, AutoCSR):
    def __init__(self, k2mm : K2MM, dw=32):
        self.source_ctrl = Endpoint(k2mm.sink_tester_ctrl.description)
        self._probe_len = CSRStorage(
            description = "Test frame length",
            fields = [
                CSRField("length", size=16, description="Test frame length"),
            ],
            name="prb_length")
        self._probe_ctrl = CSRStorage(
            description = "Test frame enable",
            fields = [
                CSRField("enable", size=1,  description="Send test frame")
            ],
            name = "prb_ctrl")
        self._probe_status = CSRStatus(
            description = "Probe status",
            fields = [
                CSRField("ready",  size=1, description="1 = Test frame command ready"),
            ],
            name="prb_stat"
        )

        self.comb += [
            self.source_ctrl.length.eq(self._probe_len.fields.length),
            self._probe_status.fields.ready.eq(self.source_ctrl.ready),
            self.source_ctrl.valid.eq(self._probe_ctrl.fields.enable & self._probe_ctrl.re)
        ]
