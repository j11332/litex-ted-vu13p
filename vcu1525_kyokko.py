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
from cores.kyokko.kyokko import Kyokko

class _CRG(Module):
    def __init__(self, platform : Platform, sys_clk_freq):
        self.rst = Signal()
        self.clock_domains.cd_sys    = ClockDomain()
        self.clock_domains.cd_sys4x  = ClockDomain(reset_less=True)
        self.clock_domains.cd_pll4x  = ClockDomain(reset_less=True)
        self.clock_domains.cd_idelay = ClockDomain()
        self.clock_domains.cd_clk100 = ClockDomain()
        # PLL
        self.submodules.pll = pll = USMMCM(speedgrade=-2)
        pll.register_clkin(platform.request("sys_clk", 0), 300e6)
        pll.create_clkout(self.cd_pll4x, sys_clk_freq*4, buf=None, with_reset=False)
        pll.create_clkout(self.cd_idelay, 500e6)
        pll.create_clkout(self.cd_clk100, 100e6, buf="bufg", with_reset=True)
                
        platform.add_false_path_constraints(self.cd_sys.clk, pll.clkin) # Ignore sys_clk to pll.clkin path created by SoC's rst.
        platform.add_false_path_constraints(self.cd_sys.clk, pll.clkin)
        
        self.comb += pll.reset.eq(self.rst)

        self.specials += [
            Instance("BUFGCE_DIV", name="main_bufgce_div",
                p_BUFGCE_DIVIDE=4,
                i_CE=1, i_I=self.cd_pll4x.clk, o_O=self.cd_sys.clk),
            Instance("BUFGCE", name="main_bufgce",
                i_CE=1, i_I=self.cd_pll4x.clk, o_O=self.cd_sys4x.clk),
        ]

        self.submodules.idelayctrl = USIDELAYCTRL(cd_ref=self.cd_idelay, cd_sys=self.cd_sys)
        

class BaseSoC(SoCCore):
    def __init__(self, sys_clk_freq=int(125e6), disable_sdram=False, **kwargs):
        platform = Platform()

        SoCCore.__init__(self, platform, sys_clk_freq,
            ident          = "LiteX SoC on tfoil",
            ident_version  = True,
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
        
        self.submodules.kyokko_phy = kyokko_phy = USPGTY4(
            platform, 
            "kyokko_phy", 
            platform.request("qsfp0_refclk161m"),
            platform.request("qsfp", 0))
        
        self.submodules.kyokko = kyokko = Kyokko(platform, kyokko_phy)
        kyokko.add_sources(platform)
                
def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on vcu1525")
    parser.add_argument("--build",        action="store_true", help="Build bitstream")
    parser.add_argument("--load",         action="store_true", help="Load bitstream")
    parser.add_argument("--sys-clk-freq", default=125e6,       help="System clock frequency (default: 200MHz)")
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
    builder.build(run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".bit"))

if __name__ == "__main__":
    main()
