#!/usr/bin/env python3

#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2020 Fei Gao <feig@princeton.edu>
# Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import os
import argparse

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.fhdl.structure import Cat
from litex_boards.platforms import ted_tfoil
from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.led import LedChaser
from litex.soc.cores.bitbang import I2CMaster
from litex.soc.cores.gpio import GPIOOut, GPIOIn
from cores.i2c_multiport import I2CMasterMP

from litedram.modules import MT40A1G8
from litedram.phy import usddrphy
from cores.ibert.ibert import IBERT

from localbuilder import LocalBuilder

# CRG
class _CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.rst = Signal()
        self.clock_domains.cd_sys    = ClockDomain()
        self.clock_domains.cd_sys4x  = ClockDomain(reset_less=True)
        self.clock_domains.cd_pll4x  = ClockDomain(reset_less=True)
        self.clock_domains.cd_idelay = ClockDomain()

        self.submodules.pll = pll = USMMCM(speedgrade=-2)
        self.comb += pll.reset.eq((~platform.request("cpu_resetn")) | self.rst)
        pll.register_clkin(platform.request("sys_clk_0"), 200e6)
        pll.create_clkout(self.cd_pll4x, sys_clk_freq*4, buf=None, with_reset=False)
        pll.create_clkout(self.cd_idelay, 400e6)
        platform.add_false_path_constraints(self.cd_sys.clk, pll.clkin) # Ignore sys_clk to pll.clkin path created by SoC's rst.

        self.specials += [
            Instance("BUFGCE_DIV", name="main_bufgce_div",
                p_BUFGCE_DIVIDE=4,
                i_CE=1, i_I=self.cd_pll4x.clk, o_O=self.cd_sys.clk),
            Instance("BUFGCE", name="main_bufgce",
                i_CE=1, i_I=self.cd_pll4x.clk, o_O=self.cd_sys4x.clk),
        ]

        self.submodules.idelayctrl = USIDELAYCTRL(cd_ref=self.cd_idelay, cd_sys=self.cd_sys)

class BaseSoC(SoCCore):
    def __init__(self, sys_clk_freq=int(200e6), disable_sdram=False, **kwargs):
        platform = ted_tfoil.Platform()

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
                    module        = MT40A1G8(sys_clk_freq, "1:4"),
                    size          = 0x40000000,
                    l2_cache_size = kwargs.get("l2_size", 8192)
                )

        self.submodules.leds = LedChaser(
            pads         = platform.request_all("user_led"),
            sys_clk_freq = sys_clk_freq)

        i2c_master_pads = [
            platform.request("i2c_tca9555", 0),
            platform.request("i2c_tca9555", 1),
            platform.request("i2c_tca9555", 2),
            platform.request("i2c_tca9555", 3),
            platform.request("i2c_tca9555", 4),
            platform.request("i2c_tca9555", 5),
            platform.request("i2c_tca9555", 6),
            platform.request("i2c_tca9548", 0),
            platform.request("i2c_tca9548", 1),
            platform.request("i2c_tca9548", 2),
            platform.request("i2c_tca9548", 3),
            platform.request("i2c_si5341", 0),
            platform.request("i2c_si5341", 1),
        ]

        self.submodules.i2c = I2CMasterMP(platform, i2c_master_pads)

        self.submodules.sb_tca9548 = GPIOOut(pads = platform.request_all("tca9548_reset_n"))

        sb_si5341_o_pads = Cat([
            platform.request("si5341_in_sel_0", 0),
            platform.request("si5341_in_sel_0", 1),
            platform.request("si5341_syncb", 0),
            platform.request("si5341_syncb", 1),
            platform.request("si5341_rstb", 0),
            platform.request("si5341_rstb", 1),
        ])
        sb_si5341_i_pads = Cat([
            platform.request("si5341_lolb", 0),
            platform.request("si5341_lolb", 1),
        ])
        self.submodules.sb_si5341_o = GPIOOut(pads = sb_si5341_o_pads)
        self.submodules.sb_si5341_i = GPIOIn(pads = sb_si5341_i_pads)
        self.submodules.ibert = IBERT(
            self.platform,
            "ibert_0",
            [
                [platform.request("MGTREFCLK_120_", 0), platform.request("MGTREFCLK_120_", 1)],
                [platform.request("MGTREFCLK_121_", 0), platform.request("MGTREFCLK_121_", 1)],
            ],
            [platform.request("GTY120"), platform.request("GTY121")],
            ip_params=platform.ip_presets['ibert']
        )

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on tfoil")
    parser.add_argument("--build",        action="store_true", help="Build bitstream")
    parser.add_argument("--load",         action="store_true", help="Load bitstream")
    parser.add_argument("--sys-clk-freq", default=200e6,       help="System clock frequency (default: 200MHz)")
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
