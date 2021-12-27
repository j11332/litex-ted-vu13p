from migen import *
from litex.soc.interconnect.stream import Endpoint
from litex.soc.interconnect.packet import *
from litex.soc.interconnect.csr_eventmanager import AutoCSR, CSRStatus, CSRStorage, CSRField
from cores.tf.packet import K2MMPacket, EbRecord, EbRecordMM

class EbRecordReceiver(Module):
    def __init__(self, dw, aw, buffer_depth=4):
        self.sink   = sink   = stream.Endpoint(EbRecord.description(dw))
        self.source = source = stream.Endpoint(EbRecordMM.description(dw, aw=aw))

        # # #

        self.submodules.fifo = fifo = PacketFIFO(EbRecord.description(dw),
            payload_depth = buffer_depth,
            param_depth   = 1,
            buffered      = True
        )
        self.comb += sink.connect(fifo.sink)

        base_addr = Signal(aw, reset_less=True)
        base_addr_update = Signal()
        self.sync += If(base_addr_update, base_addr.eq(fifo.source.data))

        count = Signal(max=512, reset_less=True)

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            fifo.source.ready.eq(1),
            NextValue(count, 0),
            If(fifo.source.valid,
                base_addr_update.eq(1),
                If(fifo.source.wcount,
                    NextState("RECEIVE_WRITES")
                ).Elif(fifo.source.rcount,
                    NextState("RECEIVE_READS")
                )
            )
        )
        fsm.act("RECEIVE_WRITES",
            source.valid.eq(fifo.source.valid),
            source.last.eq(count == fifo.source.wcount-1),
            source.count.eq(fifo.source.wcount),
            source.be.eq(fifo.source.byte_enable),
            source.addr.eq(base_addr[log2_int(aw):] + count),
            source.we.eq(1),
            source.data.eq(fifo.source.data),
            fifo.source.ready.eq(source.ready),
            If(source.valid & source.ready,
                NextValue(count, count + 1),
                If(source.last,
                    If(fifo.source.rcount,
                        NextState("RECEIVE_BASE_RET_ADDR")
                    ).Else(
                        NextState("IDLE")
                    )
                )
            )
        )
        fsm.act("RECEIVE_BASE_RET_ADDR",
            NextValue(count, 0),
            If(fifo.source.valid,
                base_addr_update.eq(1),
                NextState("RECEIVE_READS")
            )
        )
        fsm.act("RECEIVE_READS",
            source.valid.eq(fifo.source.valid),
            source.last.eq(count == fifo.source.rcount-1),
            source.count.eq(fifo.source.rcount),
            source.base_addr.eq(base_addr),
            source.addr.eq(fifo.source.data[log2_int(aw):]),
            fifo.source.ready.eq(source.ready),
            If(source.valid & source.ready,
                NextValue(count, count + 1),
                If(source.last,
                    NextState("IDLE")
                )
            )
        )

class EbRecordSender(Module):
    def __init__(self, dw, aw, buffer_depth=4):
        self.sink   = sink   = stream.Endpoint(EbRecordMM.description(dw, aw=aw))
        self.source = source = stream.Endpoint(EbRecord.description(dw))

        # # #

        self.submodules.fifo = fifo = PacketFIFO(EbRecordMM.description(dw),
            payload_depth = buffer_depth,
            param_depth   = 1,
            buffered      = True
        )
        self.comb += sink.connect(fifo.sink)

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(fifo.source.valid,
                NextState("SEND_BASE_ADDRESS")
            )
        )
        self.comb += [
            source.byte_enable.eq(fifo.source.be),
            If(fifo.source.we,
                source.wcount.eq(fifo.source.count)
            ).Else(
                source.rcount.eq(fifo.source.count)
            )
        ]
        fsm.act("SEND_BASE_ADDRESS",
            source.valid.eq(1),
            source.last.eq(0),
            source.data.eq(fifo.source.base_addr),
            If(source.ready,
                NextState("SEND_DATA")
            )
        )
        fsm.act("SEND_DATA",
            source.valid.eq(1),
            source.last.eq(fifo.source.last),
            source.data.eq(fifo.source.data),
            If(source.valid & source.ready,
                fifo.source.ready.eq(1),
                If(source.last,
                    NextState("IDLE")
                )
            )
        )

class _EbRecordPacketizer(Packetizer):
    def __init__(self, dw):
        Packetizer.__init__(self,
            EbRecord.description(dw),
            K2MMPacket.packet_user_description(dw),
            EbRecord.header(dw))

class _EbRecordDepacketizer(Depacketizer):
    def __init__(self, dw):
        Depacketizer.__init__(self,
            K2MMPacket.packet_user_description(dw),
            EbRecord.description(dw),
            EbRecord.header(dw))

from litex.soc.interconnect import wishbone
class _EbRecordWbMaster(Module):
    def __init__(self, dw, aw):
        self.sink   = sink   = stream.Endpoint(EbRecordMM.description(dw, aw))
        self.source = source = stream.Endpoint(EbRecordMM.description(dw, aw))
        self.bus    = bus    = wishbone.Interface(adr_width=aw, data_width=dw)

        # # #

        data_update = Signal()

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            sink.ready.eq(1),
            If(sink.valid,
                sink.ready.eq(0),
                If(sink.we,
                    NextState("WRITE_DATA")
                ).Else(
                    NextState("READ_DATA")
                )
            )
        )
        fsm.act("WRITE_DATA",
            bus.adr.eq(sink.addr),
            bus.dat_w.eq(sink.data),
            bus.sel.eq(sink.be),
            bus.stb.eq(sink.valid),
            bus.we.eq(1),
            bus.cyc.eq(1),
            If(bus.stb & bus.ack,
                sink.ready.eq(1),
                If(sink.last,
                    NextState("IDLE")
                )
            )
        )
        fsm.act("READ_DATA",
            bus.adr.eq(sink.addr),
            bus.sel.eq(sink.be),
            bus.stb.eq(sink.valid),
            bus.cyc.eq(1),
            If(bus.stb & bus.ack,
                data_update.eq(1),
                NextState("SEND_DATA")
            )
        )
        self.sync += [
            sink.connect(source, keep={
                "base_addr",
                "addr",
                "count",
                "be"}),
            source.we.eq(1),
            If(data_update, source.data.eq(bus.dat_r))
        ]
        fsm.act("SEND_DATA",
            sink.connect(source, keep={"valid", "last", "last_be", "ready"}),
            If(source.valid & source.ready,
                If(source.last,
                    NextState("IDLE")
                ).Else(
                    NextState("READ_DATA")
                )
            )
        )

class _EbRecordWbSlave(Module):
    def __init__(self, dw, aw):
        self.bus    = bus    = wishbone.Interface(data_width=dw, adr_width=aw)
        self.sink   = sink   = stream.Endpoint(EbRecord.description(dw))
        self.source = source = stream.Endpoint(EbRecord.description(dw))

        # # #

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            sink.ready.eq(1),
            If(bus.stb & bus.cyc,
                If(bus.we,
                    NextState("SEND_WRITE")
                ).Else(
                    NextState("SEND_READ")
                )
            )
        )
        fsm.act("SEND_WRITE",
            source.valid.eq(1),
            source.last.eq(1),
            source.last_be.eq(1 << 3),
            source.base_addr[2:].eq(bus.adr),
            source.count.eq(1),
            source.be.eq(bus.sel),
            source.we.eq(1),
            source.data.eq(bus.dat_w),
            If(source.valid & source.ready,
                bus.ack.eq(1),
                NextState("IDLE")
            )
        )
        fsm.act("SEND_READ",
            source.valid.eq(1),
            source.last.eq(1),
            source.last_be.eq(1 << 3),
            source.base_addr.eq(0),
            source.count.eq(1),
            source.be.eq(bus.sel),
            source.we.eq(0),
            source.data[2:].eq(bus.adr),
            If(source.valid & source.ready,
                NextState("WAIT_READ")
            )
        )
        fsm.act("WAIT_READ",
            sink.ready.eq(1),
            If(sink.valid & sink.we,
                bus.ack.eq(1),
                bus.dat_r.eq(sink.data),
                NextState("IDLE")
            )
        )
from litepcie.common import get_bar_mask, phy_layout, MB
from litepcie.core import LitePCIeEndpoint
from litepcie.frontend.dma import LitePCIeDMAWriter, LitePCIeDMAReader
from cores.dma.mm2s import DMARam

class _StubPHY(Module):
    def __init__(self, data_width, id, bar0_size, debug):
        self.data_width = data_width
        self.id = id
        
        self.phy_sink = stream.Endpoint(phy_layout(data_width))
        self.phy_source = stream.Endpoint(phy_layout(data_width))
        
        # Application I/F
        self.sink = stream.Endpoint(phy_layout(data_width))
        self.source = stream.Endpoint(phy_layout(data_width))

        self.bar0_size = bar0_size
        self.bar0_mask = get_bar_mask(bar0_size)

        self.max_request_size = Signal(10, reset=512)
        self.max_payload_size = Signal(8, reset=128)

        self.submodules.fifo_sink = stream.SyncFIFO(phy_layout(data_width), depth=16)
        self.submodules.fifo_source = stream.SyncFIFO(phy_layout(data_width), depth=16)
        self.comb += [
            self.fifo_sink.source.connect(self.phy_source),
            self.phy_sink.connect(self.fifo_source.sink),
            self.sink.connect(self.fifo_sink.sink),
            self.fifo_source.source.connect(self.source),
        ]
    
# DMA Memory
class DMAMem(Module, AutoCSR):
    def __init__(self, data_width, id, test_size, phy_debug = False):
        self.submodules.phy = phy = _StubPHY(data_width, id, 1 * MB, phy_debug)
        self.phy_source, self.phy_sink = phy.phy_source, phy.phy_sink
        self.submodules.endpoint = endpoint = LitePCIeEndpoint(phy)
        
        port = endpoint.crossbar.get_slave_port(lambda a: 1)
        self.submodules.dmaram = dmaram = DMARam(data_width, test_size)
        self.comb += [
            dmaram.source.connect(port.source),
            port.sink.connect(dmaram.sink)
        ]
        dma_reader_port = endpoint.crossbar.get_master_port(read_only=True)
        dma_writer_port = endpoint.crossbar.get_master_port(write_only=True)

        self.submodules.dma_reader = LitePCIeDMAReader(self.endpoint, dma_reader_port)
        self.submodules.dma_writer = LitePCIeDMAWriter(self.endpoint, dma_writer_port)
        self.comb += self.dma_reader.source.connect(self.dma_writer.sink)

class K2MMEbRecord(Module, AutoCSR):
    def __init__(self, dw, aw, id=0, endianness="big", buffer_depth=4, mode="master"):
        self.sink   = sink   = stream.Endpoint(K2MMPacket.packet_user_description(dw))
        self.source = source = stream.Endpoint(K2MMPacket.packet_user_description(dw))

        # # #
        
        self.submodules.dmamem = dmamem = DMAMem(dw, id, 1024)
        self.comb += [
            dmamem.phy_source.connect(source, keep={"valid", "ready", "last", "first"}),
            source.data.eq(dmamem.phy_source.dat),
            source.last_be.eq(dmamem.phy_source.be),
            sink.connect(dmamem.phy_sink, keep={"valid", "ready", "last", "first"}),
            dmamem.phy_sink.dat.eq(sink.data),
            dmamem.phy_sink.be.eq(sink.last_be),
        ]