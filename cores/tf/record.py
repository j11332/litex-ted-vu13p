from migen import *
from litex.soc.interconnect.stream import Endpoint
from litex.soc.interconnect.packet import *

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

class K2MMEbRecord(Module):
    def __init__(self, dw, aw, endianness="big", buffer_depth=4, mode="master"):
        self.sink   = sink   = stream.Endpoint(K2MMPacket.packet_user_description(dw))
        self.source = source = stream.Endpoint(K2MMPacket.packet_user_description(dw))

        # # #

        # Receive record, decode it and generate mmap stream
        self.submodules.depacketizer = depacketizer = _EbRecordDepacketizer(dw)
        self.submodules.receiver = receiver = EbRecordReceiver(dw, aw, buffer_depth)
        self.comb += [
            sink.connect(depacketizer.sink),
            depacketizer.source.connect(receiver.sink)
        ]
        if endianness == "big":
            self.comb += receiver.sink.data.eq(reverse_bytes(depacketizer.source.data))

        # Save last ip address
        first = Signal(reset=1)
        last_ip_address = Signal(32, reset_less=True)
        self.sync += [
            If(sink.valid & sink.ready,
                If(first, last_ip_address.eq(sink.ip_address)),
                first.eq(sink.last)
            )
        ]

        # Receive MMAP stream, encode it and send records
        self.submodules.sender     = sender     = EbRecordSender(dw, aw, buffer_depth)
        self.submodules.packetizer = packetizer = _EbRecordPacketizer(dw)
        self.comb += [
            sender.source.connect(packetizer.sink),
            packetizer.source.connect(source),
            source.length.eq(EbRecord.header(dw).length +
                (sender.source.wcount != 0) * (aw // 8) + sender.source.wcount * (dw // 8) +
                (sender.source.rcount != 0) * (aw // 8) + sender.source.rcount * (dw // 8)),
            source.ip_address.eq(last_ip_address)
        ]
        if endianness == "big":
            self.comb += packetizer.sink.data.eq(reverse_bytes(sender.source.data))

        self.submodules.wb = wb = {
            "master" : _EbRecordWbMaster,
            "slave"  : _EbRecordWbSlave
        }[mode](dw, aw)
        self.comb += [
            receiver.source.connect(wb.sink),
            wb.source.connect(sender.sink),
        ]
