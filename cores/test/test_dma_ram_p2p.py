#
# This file is part of LitePCIe.
#
# Copyright (c) 2015-2018 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

# In this high level test, LitePCIeEndpoint is connected to LitePCIeDMAReader and LitePCIeDMAWriter
# frontends with Reader's source connected to Writer's sink. Our Host model is used to emulate a Host
# memory with the Reader and Writer are reading/writing data from/to this memory. The Host memory
# is initially filled with random data, that are read by the Reader, re-directed to the Writer and
# then re-written in another memory location of the Host. The test then checks that the initial data
# and re-written data are identical.

import unittest

from litex.soc.interconnect import wishbone

from litepcie.common import *
from litepcie.core import LitePCIeEndpoint
from litepcie.core.msi import LitePCIeMSI
from litepcie.frontend.dma import LitePCIeDMAWriter, LitePCIeDMAReader
from cores.dma.mm2s import DMARam

root_id     = 0x100
endpoint_id = 0x400

def seed_to_data(seed, random=True):
    if random:
        return (seed * 0x31415979 + 1) & 0xffffffff
    else:
        return seed

class DMADriver:
    """DMA Driver model

    Provides methods to control/program LitePCIeDMAReader/LitePCIeDMAWriter.
    """
    def __init__(self, dma, dut):
        self.dma = getattr(dut, dma)
        self.dut = dut

    def set_prog_mode(self):
        yield from self.dma.table.loop_prog_n.write(0)

    def set_loop_mode(self):
        yield from self.dma.table.loop_prog_n.write(1)

    def flush(self):
        yield from self.dma.table.reset.write(1)

    def program_descriptor(self, address, length):
        value = address
        value |= (length << 32)
        yield from self.dma.table.value.write(value)
        yield from self.dma.table.we.write(1)

    def enable(self):
        yield from self.dma.enable.write(1)

    def disable(self):
        yield from self.dma.enable.write(0)

class _StubPHY(Module):
    def __init__(self, data_width, id, bar0_size, debug):
        self.data_width = data_width

        self.id = id

        self.bar0_size = bar0_size
        self.bar0_mask = get_bar_mask(bar0_size)

        self.max_request_size = Signal(10, reset=512)
        self.max_payload_size = Signal(8, reset=128)
        
        self.sink = stream.Endpoint(phy_layout(data_width))
        self.source = stream.Endpoint(phy_layout(data_width))
        self.submodules.fifo_sink = stream.SyncFIFO(phy_layout(data_width), depth=16)
        self.submodules.fifo_source = stream.SyncFIFO(phy_layout(data_width), depth=16)
        self.comb += [
            self.sink.connect(self.fifo_sink.sink),
            self.fifo_source.source.connect(self.source),
        ]
    
# DMA Memory
class _DMAMem(Module):
    def __init__(self, data_width, id, test_size, phy_debug = False):
        self.submodules.phy = phy = _StubPHY(data_width, id, 1 * MB, phy_debug)
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

class DUT(Module):
    def __init__(self, data_width, test_size=1024):
        self.submodules.memory = mem = _DMAMem(data_width, endpoint_id, test_size)
        self.submodules.memory_peer = mem_peer = _DMAMem(data_width, endpoint_id + 1, test_size)
        self.comb += [
            # mem | -> | dut
            mem.phy.fifo_sink.source.connect(mem_peer.phy.fifo_source.sink),
            mem_peer.phy.fifo_sink.source.connect(mem.phy.fifo_source.sink),
        ]
        self.monitor_eps = {
            "phy_src"         : mem.phy.source,
            "phy_snk"         : mem.phy.sink,
            "depacketizer_in" : mem.endpoint.depacketizer.sink,
            "req_source"      : mem.endpoint.depacketizer.req_source,
            "cmp_source"      : mem.endpoint.depacketizer.cmp_source,
            "req_sink"        : mem.endpoint.packetizer.req_sink,
            "cmp_sink"        : mem.endpoint.packetizer.cmp_sink,
            "packetizer_out"  : mem.endpoint.packetizer.source,
            "mem_depacketizer_in" : mem_peer.endpoint.depacketizer.sink,
            "mem_req_source"      : mem_peer.endpoint.depacketizer.req_source,
            "mem_cmp_source"      : mem_peer.endpoint.depacketizer.cmp_source,
            "mem_req_sink"        : mem_peer.endpoint.packetizer.req_sink,
            "mem_cmp_sink"        : mem_peer.endpoint.packetizer.cmp_sink,
            "mem_packetizer_out"  : mem_peer.endpoint.packetizer.source,
            "dmaram_sink"         : mem_peer.dmaram.sink,
            "dmaram_source"       : mem_peer.dmaram.source,
        }
        
class TestDMA(unittest.TestCase):
    def dma_test(self, data_width, test_size=1024, vcd_name = ""):
        host_data     = [seed_to_data(i, True) for i in range(test_size//4)]
        loopback_data = []

        def main_generator(dut, nreads=8, nwrites=8):

            # DMA Reader/Writer control models
            dma_reader_driver = DMADriver("dma_reader", dut.memory)
            dma_writer_driver = DMADriver("dma_writer", dut.memory)

            # Program DMA Reader descriptors
            yield from dma_reader_driver.set_prog_mode()
            yield from dma_reader_driver.flush()
            for i in range(nreads):
                yield from dma_reader_driver.program_descriptor((test_size//8)*i, test_size//8)

            # Program DMA Writer descriptors
            yield from dma_writer_driver.set_prog_mode()
            yield from dma_writer_driver.flush()
            for i in range(nwrites):
                yield from dma_writer_driver.program_descriptor(test_size + (test_size//8)*i, test_size//8)

            # Enable DMA Reader & Writer
            yield from dma_reader_driver.enable()
            yield from dma_writer_driver.enable()
            
            # Delay to ensure all the data has been written
            for i in range(1024):
                yield
                
        generate_dut = lambda: DUT(data_width)

        # Generate gtkwave save file
        dut = generate_dut()
        from migen.fhdl import verilog
        from litex.build.sim import gtkwave as gtkw
        import os.path
        
        vns = verilog.convert(dut).ns
        with gtkw.GTKWSave(vns, os.path.splitext(vcd_name)[0] + ".gtkw", vcd_name, prefix="DUT.") as s:
            s.clocks()            
            for key, ep in dut.monitor_eps.items():
                s.add(ep, group_name=key)
        
        # Simulation
        dut = generate_dut()        
        generators = {
            "sys" : [
                main_generator(dut),
            ]
        }
        clocks = {"sys": 10}
        run_simulation(dut, generators, clocks, vcd_name=vcd_name)

    def test_dma_256b(self):
        self.dma_test(256, vcd_name="dma_ram_test_256b.vcd")