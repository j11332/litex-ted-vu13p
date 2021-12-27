import bitarray
import bitarray.util
import math
from cores.tf.packet import K2MMPacket, EbRecordMM, EbRecord

def pack_uint(_v, _width):
    return bitarray.util.int2ba(_v, length=_width).tobytes()

def unpack_uint(b, _width):
    ba = bitarray.bitarray()
    ba.pack(b)
    return bitarray.util.ba2int(ba)

def _merge_bytes(b, endianness="big"):
    return int.from_bytes(bytes(b), endianness)

def _get_field_data(field, datas):
    v = _merge_bytes(datas[field.byte:field.byte+math.ceil(field.width/8)])
    return (v >> field.offset) & (2**field.width-1)

class _PacketModel(list):
    def __init__(self, init=[]):
        self.ongoing = False
        self.done    = False
        self.bytes   = init
    def encode(self):
        pass
    def decode(self):
        pass

class EbWriteBeat:
    def __init__(self, data, width):
        self.data = data
        self.width = width

    def __repr__(self):
        _fmt = "WR 0x{"
        _fmt += f":0{self.width//8 * 2}"
        _fmt += "x}"
        return _fmt.format(self.data)

class EbReadBeat:
    def __init__(self, addr):
        self.addr = addr

    def __repr__(self):
        return "RD @ 0x{:016x}".format(self.addr)

class EbWrites(_PacketModel): 

    def __init__(self, aw, dw, init=[], base_addr=0, data=[]):
        if aw not in {32, 64}:
            raise ValueError(f"Address width must be 32 or 64.")

        if isinstance(data, list) and len(data) > 255:
            raise ValueError(f"Burst size of {len(data)} exceeds maximum of 255 allowed by Etherbone.")
        _PacketModel.__init__(self, init)
        
        self.aw = aw
        self.dw = dw
        self.base_addr = base_addr
        self.writes    = []
        self.encoded   = init != []
        
        for i in data:
            self.add(EbWriteBeat(i, self.dw))

    def add(self, write):
        self.writes.append(write)

    def get_data(self):
        data = []
        for write in self.writes:
            data.append(write.data)
        return data

    def encode(self):
        if self.encoded:
            raise ValueError
        ba = bytearray()
        ba += pack_uint(self.base_addr, self.aw)
        for write in self.writes:
            ba += pack_uint(write.data, self.dw)
        self.bytes   = ba
        self.encoded = True

    def decode(self):
        if not self.encoded:
            raise ValueError
        ba = self.bytes
        self.base_addr = unpack_uint(ba[:(self.aw // 8)])
        writes = []
        offset = self.dw // 8
        length = len(ba)
        while length > offset:
            writes.append(EbWriteBeat(unpack_uint(ba[offset:offset+(self.dw // 8)])))
            offset += (self.dw // 8)
        self.writes  = writes
        self.encoded = False

    def __repr__(self):
        r = "Writes\n"
        r += "BaseAddr @ 0x{:016x}\n".format(self.base_addr)
        for write in self.writes:
            r += write.__repr__() + "\n"
        return r

class EbReads(_PacketModel):
    def __init__(self, dw, aw, init=[], base_ret_addr=0, addrs=[]):
        if isinstance(addrs, list) and len(addrs) > 255:
            raise ValueError(f"Burst size of {len(addrs)} exceeds maximum of 255 allowed by Etherbone.")
        _PacketModel.__init__(self, init)
        self.dw = dw
        self.aw = aw
        self.base_ret_addr = base_ret_addr
        self.reads   = []
        self.encoded = init != []
        for addr in addrs:
            self.add(EbReadBeat(addr))

    def add(self, read):
        self.reads.append(read)

    def get_addrs(self):
        addrs = []
        for read in self.reads:
            addrs.append(read.addr)
        return addrs

    def encode(self):
        if self.encoded:
            raise ValueError
        ba = bytearray()
        ba += pack_uint(self.base_ret_addr, self.aw)
        for read in self.reads:
            ba += pack_uint(read.addr, self.aw)
        self.bytes   = ba
        self.encoded = True

    def decode(self):
        if not self.encoded:
            raise ValueError
        ba = self.bytes
        base_ret_addr = unpack_uint(ba[:(self.aw//8)])
        reads  = []
        offset = 4
        length = len(ba)
        while length > offset:
            reads.append(EbReadBeat(unpack_uint(ba[offset:offset+(self.dw // 8)])[0]))
            offset += (self.dw // 8)
        self.reads   = reads
        self.encoded = False

    def __repr__(self):
        r = "Reads\n"
        r += "BaseRetAddr @ 0x{:08x}\n".format(self.base_ret_addr)
        for read in self.reads:
            r += read.__repr__() + "\n"
        return r

class EbRecordModel(_PacketModel):
    def __init__(self, dw, aw, init=[]):
        _PacketModel.__init__(self, init)
        self.dw, self.aw = dw, aw
        self.writes      = None
        self.reads       = None
        self.bca         = 0
        self.rca         = 0
        self.rff         = 0
        self.cyc         = 0
        self.wca         = 0
        self.wff         = 0
        self.byte_enable = ((2 ** (dw // 8)) - 1)
        self.wcount      = 0
        self.rcount      = 0
        self.encoded     = init != []

    def decode(self):
        if not self.encoded:
            raise ValueError

        # Decode header
        header = list(self.bytes[:EbRecord.header(self.dw).length])
        for k, v in sorted(EbRecord.header(self.dw).fields.items()):
            setattr(self, k, _get_field_data(v, header))
        offset = EbRecord.header(self.dw).length

        # Decode writes
        if self.wcount:
            self.writes = EbWrites(self.bytes[offset:offset + 4*(self.wcount+1)])
            offset += 4*(self.wcount+1)
            self.writes.decode()

        # Decode reads
        if self.rcount:
            self.reads = EbReads(self.bytes[offset:offset + 4*(self.rcount+1)])
            offset += 4*(self.rcount+1)
            self.reads.decode()

        self.encoded = False

    def encode(self):
        if self.encoded:
            raise ValueError

        # Set writes/reads count
        self.wcount = 0 if self.writes is None else len(self.writes.writes)
        self.rcount = 0 if self.reads  is None else len(self.reads.reads)

        ba = bytearray()

        # Encode header
        header = 0
        for k, v in sorted(EbRecord.header(self.dw).fields.items()):
            value = int.from_bytes(getattr(self, k).to_bytes(math.ceil(v.width/8), "big"), "little")
            header += (value << v.offset+(v.byte*8))
        ba += header.to_bytes(EbRecord.header(self.dw).length, "little")

        # Encode writes
        if self.wcount:
            self.writes.encode()
            ba += self.writes.bytes

        # Encode reads
        if self.rcount:
            self.reads.encode()
            ba += self.reads.bytes

        self.bytes   = ba
        self.encoded = True

    def __repr__(self, n=0):
        r = "Record {}\n".format(n)
        r += "--------\n"
        if self.encoded:
            for d in self.bytes:
                r += "{:02x}".format(d)
        else:
            for k in sorted(EbRecord.header(self.dw).fields.keys()):
                r += k + " : 0x{:0x}\n".format(getattr(self, k))
            if self.wcount:
                r += self.writes.__repr__()
            if self.rcount:
                r += self.reads.__repr__()
        return r

class K2MMPacketModel(_PacketModel):
    def __init__(self, dw, init=[]):
        self.dw = dw

        self.header_layout = layout = K2MMPacket.get_header(dw).fields
        self.header_len = length = K2MMPacket.get_header(dw).length
        self.header = dict()
        for k, v in layout.items():
            self.header[k] = 0
        
        self.header['magic'] = K2MMPacket.magic
        from migen.fhdl.bitcontainer import log2_int
        self.header['align'] = log2_int(dw // 8)
        
        self.encoded = True if init != None else False
        self.payload = bytearray()
        _PacketModel.__init__(self, init)

    def __len__(self):
        return K2MMPacket.get_header(self.dw).length + len(self.payload)
            
    def encode(self):
        ba = bytearray()
        
        # Encode header
        header = 0
        for k, v in sorted(K2MMPacket.get_header(self.dw).fields.items()):
            value = int.from_bytes(self.header[k].to_bytes(math.ceil(v.width/8), "big"), "little")
            header += (value << v.offset+(v.byte*8))
        ba += header.to_bytes(K2MMPacket.get_header(self.dw).length, "little")
        
        if self.payload is not None:
            ba += self.payload
        
        self.bytes = ba
        self.encoded = True
    
    def decode(self):
        if not self.encoded:
            raise ValueError()
        
        # Decode header
        header = list(self.bytes[:K2MMPacket.get_header(self.dw).length])
        for k, v in sorted(K2MMPacket.get_header(self.dw).fields.items()):
            self.header[k] = _get_field_data(v, header)
        offset = K2MMPacket.get_header(self.dw).length
        
        # Decode payload
        self.payload = self.bytes[offset:]

        self.encoded = False
    
    def add_test_frame(self, length):
        #FIXME: K2MMPacket の中に移動させる
        TESTFRAME_COUNTER_LEN = 16
        if self.encoded is not True:
            raise ValueError
        for i in range(length):
            beat = bytearray()
            for j in range(self.dw // TESTFRAME_COUNTER_LEN):
                beat += i.to_bytes(TESTFRAME_COUNTER_LEN // 8, "little")
            self.payload += beat
    
    def __repr__(self):
        r = "K2MM Packet\n"
        import pprint
        r += f"{self.header}\n"
        r += "data beats:"
        ps = ""
        if self.payload is not None:
            for i, v in enumerate(self.payload):
                if i % (self.dw // 8) == 0:
                    ps += "\n"
                ps += "{:02x} ".format(v)
        r += ps
        return r
        
if __name__ == "__main__":
    from cores.tf.tests.model import EbRecordModel
    m = EbRecordModel(256, 64)
    m.bca = 1
    print(m)
    m.encode()
    print(m.bytes)
    m.decode()
    print(m)

    m.wff = 1
    m.bca = 1
    m.encode()
    print(m.bytes)
    m.decode()
    print(m)
