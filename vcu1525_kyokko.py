#!/usr/bin/env python3

import os
import argparse

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.fhdl.structure import Cat
from litex_boards.platforms.xilinx_vcu1525 import Platform
from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.led import LedChaser
from litex.soc.cores.bitbang import I2CMaster
from litex.soc.cores.gpio import GPIOOut, GPIOIn
from cores.i2c_multiport import I2CMasterMP

from litedram.modules import MTA18ASF2G72PZ
from litedram.phy import usddrphy
from localbuilder import LocalBuilder

from cores.kyokko.phy.phy_usp_gty import USPGTY4
from cores.kyokko.kyokko import KyokkoBlock
from cores.tf.framing import K2MMBlock
from litex.soc.cores.clock.common import *
from litex.soc.cores.clock.xilinx_common import *

class _MMCMReset(Module):
    def __init__(self, cd="sys"):
        self.clock_domains.cd_cfgmclk = cd_cfgmclk = ClockDomain()
        self.mmcm_reset = mmcm_reset = Signal(reset=1)
        self.startup_reset = startup_reset = Signal(reset=1)

        _cfgmclk = Signal(reset_less = True)
        _eos = Signal(reset_less = True)
        self.specials += [
            Instance("STARTUPE3", name="startupe3_inst",
                o_CFGCLK    = Signal(), # 1-bit output: Configuration main clock output.
                o_CFGMCLK   = _cfgmclk, # 1-bit output: Configuration internal oscillator clock output.
                o_DI        = Signal(4), # 4-bit output: Allow receiving on the D input pin.
                o_EOS       = _eos, # 1-bit output: Active-High output signal indicating the End Of Startup.
                o_PREQ      = Signal(), # 1-bit output: PROGRAM request to fabric output.
                i_DO        = 0, # 4-bit input: Allows control of the D pin output.
                i_DTS       = 0, # 4-bit input: Allows tristate of the D pin.
                i_FCSBO     = 0b0, # 1-bit input: Controls the FCS_B pin for flash access.
                i_FCSBTS    = 0b0, # 1-bit input: Tristate the FCS_B pin.
                i_GSR       = 0b0, # 1-bit input: Global Set/Reset input (GSR cannot be used for the port).
                i_GTS       = 0b0, # 1-bit input: Global 3-state input (GTS cannot be used for the port name).
                i_KEYCLEARB = 0b1, # 1-bit input: Clear AES Decrypter Key input from Battery-Backed RAM (BBRAM).
                i_PACK      = 0b0, # 1-bit input: PROGRAM acknowledge input.
                i_USRCCLKO  = 0b0, # 1-bit input: User CCLK input.
                i_USRCCLKTS = 0b0, # 1-bit input: User CCLK 3-state enable input.
                i_USRDONEO  = 0b0, # 1-bit input: User DONE pin output control.
                i_USRDONETS = 0b1, # 1-bit input: User DONE 3-state enable output.
            ),
            Instance("BUFG", name="buf_cfgmclk",
            i_I = _cfgmclk,
            o_O = cd_cfgmclk.clk)
        ]
        self.comb += cd_cfgmclk.rst.eq(~_eos)

        counter = Signal(10, reset=0)
        _sync = getattr(self.sync, cd_cfgmclk.name)
        from functools import reduce
        from operator import and_
        timeout = Signal()
        self.comb += [
            timeout.eq(reduce(and_, [counter[i] for i in range(len(counter))]))
        ]
        _sync += [
            counter.eq(counter + 1),
            If(timeout,
                If(mmcm_reset,
                    mmcm_reset.eq(0),
                ).Elif(startup_reset,
                    startup_reset.eq(0),
                ),
            ),
        ]

class _CRG(Module):
    def __init__(self, platform : Platform, sys_clk_freq):
        self.rst = Signal()
        self.clock_domains.cd_sys    = ClockDomain()
        self.clock_domains.cd_sys4x  = ClockDomain(reset_less=True)
        self.clock_domains.cd_pll4x  = ClockDomain(reset_less=True)
        self.clock_domains.cd_idelay = ClockDomain()
        self.clock_domains.cd_clk100  = ClockDomain()
        
        # External MMCM Reset
        self.submodules.startup = startup = _MMCMReset()
        _pads = platform.request("qsfp0_fs")
        _pads2 = platform.request("qsfp1_fs")
        self.comb += [
            _pads.fs.eq(0b10),
            _pads.rst.eq(startup.mmcm_reset),
            _pads2.fs.eq(0b10),
            _pads2.rst.eq(startup.mmcm_reset),
        ]
        self.comb += self.rst.eq(startup.startup_reset)
        platform.add_platform_command("create_clock -period 15 -name cfgmclk [get_pins startupe3_inst/CFGMCLK]")

        # PLL
        self.submodules.pll = pll = USMMCM(speedgrade=-2)
        pll.register_clkin(platform.request("sys_clk", 1), 300e6)
        pll.create_clkout(self.cd_pll4x, sys_clk_freq * 4, buf=None, with_reset=False)
        pll.create_clkout(self.cd_idelay, sys_clk_freq * 2)

        platform.add_false_path_constraints(self.cd_sys.clk, pll.clkin) # Ignore sys_clk to pll.clkin path created by SoC's rst.
        platform.add_false_path_constraints(self.cd_sys.clk, pll.clkin)
        
        self.comb += pll.reset.eq(self.rst)
        
        self.specials += [
            Instance("BUFGCE_DIV", name="buf_pll4x",
                p_BUFGCE_DIVIDE=4,
                i_CE=1, i_I=self.cd_pll4x.clk, o_O=self.cd_sys.clk),
            Instance("BUFGCE_DIV", name="buf_clk100",
                p_BUFGCE_DIVIDE=6,
                i_CE=1, i_I=self.cd_idelay.clk, o_O=self.cd_clk100.clk),
            AsyncResetSynchronizer(self.cd_clk100, self.cd_sys.rst),
            Instance("BUFGCE", name="buf_sys",
                i_CE=1, i_I=self.cd_pll4x.clk, o_O=self.cd_sys4x.clk),
        ]

        self.submodules+= USIDELAYCTRL(cd_ref=self.cd_idelay, cd_sys=self.cd_sys)

class BaseSoC(SoCCore):
    def __init__(self, sys_clk_freq=int(200e6), disable_sdram=False, **kwargs):
        platform = Platform()

        SoCCore.__init__(self, platform, sys_clk_freq,
            ident          = "LiteX SoC on tfoil",
            ident_version  = True,
            cpu_type       = "vexriscv",
            **kwargs)

        self.submodules.crg = _CRG(platform, sys_clk_freq)

        if not disable_sdram:
            if not self.integrated_main_ram_size:
                self.submodules.ddrphy = usddrphy.USPDDRPHY(platform.request("ddram"),
                    memtype          = "DDR4",
                    sys_clk_freq     = sys_clk_freq,
                    iodelay_clk_freq = 400e6)
                self.add_sdram("sdram",
                    phy           = self.ddrphy,
                    module        = MTA18ASF2G72PZ(sys_clk_freq, "1:4"),
                    size          = 0x40000000,
                    l2_cache_size = kwargs.get("l2_size", 8192)
                )

        self.add_ram("firmware_ram", 0x20000000, 0x8000)

        self.submodules.leds = LedChaser(
            pads         = platform.request_all("user_led"),
            sys_clk_freq = sys_clk_freq)
        
        self._add_kyokko(platform)

    def _add_kyokko(self, platform):
        from cores.tf.framing import K2MMControl, K2MM
        #
        # Port #1
        #
        self.submodules.ky_0 = kyokko = KyokkoBlock(
            platform, 
            platform.request("qsfp", 0),
            platform.request("qsfp0_refclk161m"),
            cd_freerun="clk100"
        )
        self.submodules.k2mm_0 = k2mm = K2MM(dw=256)
        self.comb += [
            kyokko.init_clk_locked.eq(self.crg.pll.locked),
            kyokko.source_user_rx.connect(k2mm.sink_packet_rx, omit={"last_be", "error", "src_port", "dst_port", "ip_address", "length"}),
            k2mm.source_packet_tx.connect(kyokko.sink_user_tx, omit={"last_be", "error", "src_port", "dst_port", "ip_address", "length"}),
        ]
        self.submodules.k2mmctrl_0 = k2mmctrl_0 = K2MMControl(k2mm, dw=256)
        self.comb += k2mmctrl_0.source_ctrl.connect(k2mm.sink_tester_ctrl)
        
        #
        # Port #2
        #
        self.submodules.ky_1 = ky1 = KyokkoBlock(
            platform, 
            platform.request("qsfp", 1),
            kyokko.get_refclk(),
            cd_freerun="clk100"
        )
        self.submodules.k2mm_1 = k2mm_1 = K2MM(dw=256)
        self.comb += [
            ky1.init_clk_locked.eq(self.crg.pll.locked),
            ky1.source_user_rx.connect(k2mm_1.sink_packet_rx, omit={"last_be", "error", "src_port", "dst_port", "ip_address", "length"}),
            k2mm_1.source_packet_tx.connect(ky1.sink_user_tx, omit={"last_be", "error", "src_port", "dst_port", "ip_address", "length"}),
        ]
        self.submodules.k2mmctrl_1 = k2mmctrl_1 = K2MMControl(k2mm_1, dw=256)
        self.comb += k2mmctrl_1.source_ctrl.connect(k2mm_1.sink_tester_ctrl)
        KyokkoBlock.add_common_timing_constraints(platform)

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on vcu1525")
    parser.add_argument("--build",        action="store_true", help="Build bitstream")
    parser.add_argument("--load",         action="store_true", help="Load bitstream")
    parser.add_argument("--sys-clk-freq", default=300e6,       help="System clock frequency (default: 300MHz)")
    parser.add_argument("--disable_sdram", action="store_true", help="Build without onboard memory controller (default: false)")
    builder_args(parser)
    soc_core_args(parser)
    args = parser.parse_args()

    soc = BaseSoC(
        disable_sdram = True if args.disable_sdram else False,
        sys_clk_freq = int(float(args.sys_clk_freq)),
        **soc_core_argdict(args)
    )

    builder = LocalBuilder(soc, **builder_argdict(args))
    from litex.build import tools
    soc.platform.ila.generate_ila(builder.gateware_dir)
    vns = builder.build(run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".bit"))

if __name__ == "__main__":
    main()
