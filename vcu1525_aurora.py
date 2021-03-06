#!/usr/bin/env python3

import os
import argparse

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

# LiteX specific
from litex.soc.cores.clock.common import *
from litex.soc.cores.clock.xilinx_common import *
from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.led import LedChaser

# Local source
from litex_boards.platforms.xilinx_vcu1525 import Platform
from cores.kyokko.aurora import Aurora64b66b
from util.reset import XilinxStartupReset
from localbuilder import LocalBuilder

class _CRGBlock(Module):
    """_CRGBlock
        Same as _CRG but with Xilinx Clocking Wizard IP.        

    Args:
        platform: Platform
            LiteX-boards platform object
        
        sys_clk_freq: int
            Default(sys_clk) clock frequency
            
    """
    def __init__(self, platform, sys_clk_freq):
        if sys_clk_freq is not int(300e6):
            NotImplemented("FIXME: Default clock should be 300 MHz.")
        self.locked = Signal()
        self.clock_domains.cd_sys    = ClockDomain()
        self.clock_domains.cd_clk100  = ClockDomain()
        ip_params = {
            "CONFIG.PRIMITIVE"                       : "Auto" ,
            "CONFIG.OPTIMIZE_CLOCKING_STRUCTURE_EN"  : "true" ,
            "CONFIG.PRIM_SOURCE"                     : "Differential_clock_capable_pin" ,
            "CONFIG.PRIM_IN_FREQ"                    : "300" ,
            "CONFIG.CLKOUT2_USED"                    : "true" ,
            "CONFIG.CLKOUT3_USED"                    : "true" ,
            "CONFIG.CLK_OUT1_PORT"                   : "clk_sys" ,
            "CONFIG.CLK_OUT2_PORT"                   : "clk_100" ,
            "CONFIG.CLK_OUT3_PORT"                   : "clk_init" ,
            "CONFIG.CLKOUT1_REQUESTED_OUT_FREQ"      : "300.000" ,
            "CONFIG.CLKOUT2_REQUESTED_OUT_FREQ"      : "100.000" ,
            "CONFIG.CLKOUT3_REQUESTED_OUT_FREQ"      : "50.000" ,
            "CONFIG.USE_SAFE_CLOCK_STARTUP"          : "true" ,
            "CONFIG.USE_LOCKED"                      : "true" ,
            "CONFIG.USE_RESET"                       : "true" ,
            "CONFIG.USE_INCLK_STOPPED"               : "false" ,
            "CONFIG.RESET_TYPE"                      : "ACTIVE_HIGH" ,
            "CONFIG.CLKIN1_JITTER_PS"                : "33.330000000000005" ,
            "CONFIG.CLKOUT1_DRIVES"                  : "BUFGCE" ,
            "CONFIG.CLKOUT2_DRIVES"                  : "BUFGCE" ,
            "CONFIG.CLKOUT3_DRIVES"                  : "BUFGCE" ,
            "CONFIG.CLKOUT4_DRIVES"                  : "BUFGCE" ,
            "CONFIG.CLKOUT5_DRIVES"                  : "BUFGCE" ,
            "CONFIG.CLKOUT6_DRIVES"                  : "BUFGCE" ,
            "CONFIG.CLKOUT7_DRIVES"                  : "BUFGCE" ,
            "CONFIG.FEEDBACK_SOURCE"                 : "FDBK_AUTO" ,
            "CONFIG.MMCM_DIVCLK_DIVIDE"              : "1" ,
            "CONFIG.MMCM_BANDWIDTH"                  : "OPTIMIZED" ,
            "CONFIG.MMCM_CLKFBOUT_MULT_F"            : "4.000" ,
            "CONFIG.MMCM_CLKIN1_PERIOD"              : "3.333" ,
            "CONFIG.MMCM_CLKIN2_PERIOD"              : "10.0" ,
            "CONFIG.MMCM_COMPENSATION"               : "AUTO" ,
            "CONFIG.MMCM_CLKOUT0_DIVIDE_F"           : "4.000" ,
            "CONFIG.MMCM_CLKOUT1_DIVIDE"             : "12" ,
            "CONFIG.MMCM_CLKOUT2_DIVIDE"             : "24" ,
            "CONFIG.NUM_OUT_CLKS"                    : "3" ,
            "CONFIG.RESET_PORT"                      : "reset" ,
            "CONFIG.CLKOUT1_JITTER"                  : "81.814" ,
            "CONFIG.CLKOUT1_PHASE_ERROR"             : "77.836" ,
            "CONFIG.CLKOUT2_JITTER"                  : "101.475" ,
            "CONFIG.CLKOUT2_PHASE_ERROR"             : "77.836" ,
            "CONFIG.CLKOUT3_JITTER"                  : "116.415" ,
            "CONFIG.CLKOUT3_PHASE_ERROR"             : "77.836" ,
            "CONFIG.AUTO_PRIMITIVE"                  : "MMCM" 
        }
        platform.add_tcl_ip("xilinx.com:ip:clk_wiz", "crg_clkgen", ip_params)
        pads = platform.request("sys_clk", 1)

        self.submodules.startup = startup = XilinxStartupReset()
        self.specials += Instance(
            "crg_clkgen",
            i_clk_in1_p = pads.p,
            i_clk_in1_n = pads.n,
            i_reset     = startup.cd_cfgmclk_mmcm.rst,
            o_locked    = self.locked,
            o_clk_sys   = self.cd_sys.clk,
            o_clk_100   = self.cd_clk100.clk,
        )
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~self.locked)
        self.specials += AsyncResetSynchronizer(self.cd_clk100, ~self.locked)
        for _pn in ["qsfp0_fs", "qsfp1_fs"]:
            _pads = platform.request(_pn)
            self.comb += [
                _pads.fs.eq(0b10),
                _pads.rst.eq(startup.cd_cfgmclk_por.rst),
            ]

class _CRG(Module):
    def __init__(self, platform : Platform, sys_clk_freq):
        self.rst = Signal(reset_less=True)
        self.locked = Signal(reset_less=True)
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_clk100 = ClockDomain()
        self.clock_domains.cd_idelay = ClockDomain()
        
        # External clock reset
        #               |_20us_|
        # QSFP0/1 reset |      \___________
        #               |______|_20us_
        # FPGA MMCM rst |      |      \____
        self.submodules.startup = startup = XilinxStartupReset()
        for _pn in range(0, 2):
            _pads = platform.request("qsfp_fs", _pn)
            self.comb += [
                _pads.fs.eq(0b10),
                _pads.rst.eq(startup.cd_cfgmclk_por.rst),
            ]

        platform.add_platform_command(
            "create_clock -period 20 -name cfgmclk "
            "[get_pins startupe3_inst/CFGMCLK]")

        # PLL
        self.submodules.pll = pll = USMMCM(speedgrade=-2)
        pll.register_clkin(platform.request("sys_clk", 1), 300e6)
        pll.create_clkout(self.cd_sys,    sys_clk_freq, with_reset=False)
        pll.create_clkout(self.cd_clk100, 100e6,        with_reset=False)
        pll.create_clkout(self.cd_idelay, 400e6)
        self.comb += [
            self.locked.eq(pll.locked),
            pll.reset.eq(self.rst),
            self.rst.eq(startup.cd_cfgmclk_mmcm.rst)
        ]

        # Ignore sys_clk to pll.clkin path created by SoC's rst.
        platform.add_false_path_constraints(self.cd_sys.clk, pll.clkin)
        
        self.specials += [
            AsyncResetSynchronizer(self.cd_clk100, ~self.locked),
        ]
        self.submodules += USIDELAYCTRL(cd_ref=self.cd_idelay, cd_sys=self.cd_sys)

class BaseSoC(SoCCore):
    def __init__(self, sys_clk_freq=int(200e6), disable_sdram=False, use_clkwiz = False, **kwargs):
        platform = Platform()

        SoCCore.__init__(self, platform, sys_clk_freq,
            ident          = "LiteX SoC on tfoil",
            ident_version  = True,
            cpu_type       = "vexriscv",
            **kwargs)

        crg = _CRGBlock(platform, sys_clk_freq) if use_clkwiz else _CRG(platform, sys_clk_freq)
        self.submodules.crg = crg
        
        if not disable_sdram:
            if not self.integrated_main_ram_size:
                NotImplementedError()

        self.add_ram("firmware_ram", 0x20000000, 0x8000)

        self.submodules.leds = LedChaser(
            pads         = platform.request_all("user_led"),
            sys_clk_freq = sys_clk_freq)
        
        self._add_aurora(platform)

    def _add_aurora(self, platform):
        from cores.tf.framing import K2MMControl, K2MM
        # Port #1
        self.submodules.ky_0 = kyokko = Aurora64b66b(
            platform,
            platform.request("qsfp", 0),
            platform.request("qsfp0_refclk1"),
            cd_freerun="clk100",
        )
        self.submodules.k2mm_0 = k2mm = K2MM(dw=256)
        self.comb += [
            kyokko.init_clk_locked.eq(self.crg.locked),
            kyokko.source_user_rx.connect(k2mm.sink_packet_rx, omit={"last_be", "error", "src_port", "dst_port", "ip_address", "length"}),
            k2mm.source_packet_tx.connect(kyokko.sink_user_tx, omit={"last_be", "error", "src_port", "dst_port", "ip_address", "length"}),
        ]
        self.submodules.k2mmctrl_0 = k2mmctrl_0 = K2MMControl(k2mm, dw=256)
        self.comb += k2mmctrl_0.source_ctrl.connect(k2mm.sink_tester_ctrl)

        self.submodules.ky_1 = ky1 = Aurora64b66b(
            platform, 
            platform.request("qsfp", 1),
            platform.request("qsfp1_refclk1"),
            cd_freerun="clk100",
            with_ila=False
        )
        self.submodules.k2mm_1 = k2mm_1 = K2MM(dw=256)
        self.comb += [
            ky1.init_clk_locked.eq(self.crg.locked),
            ky1.source_user_rx.connect(k2mm_1.sink_packet_rx, omit={"last_be", "error", "src_port", "dst_port", "ip_address", "length"}),
            k2mm_1.source_packet_tx.connect(ky1.sink_user_tx, omit={"last_be", "error", "src_port", "dst_port", "ip_address", "length"}),
        ]
        self.submodules.k2mmctrl_1 = k2mmctrl_1 = K2MMControl(k2mm_1, dw=256)
        self.comb += k2mmctrl_1.source_ctrl.connect(k2mm_1.sink_tester_ctrl)

        from cores.qsfp_sideband import QSFPSidebandRegister
        self.submodules.qsfp0_ls = QSFPSidebandRegister(platform.request("qsfp_ls", 0))
        self.submodules.qsfp1_ls = QSFPSidebandRegister(platform.request("qsfp_ls", 1))

    def do_finalize(self):
        self.platform.finalize_tcl_ip()
        SoCCore.do_finalize(self)

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on vcu1525")
    parser.add_argument("--build",          action="store_true", help="Build bitstream")
    parser.add_argument("--load",           action="store_true", help="Load bitstream")
    parser.add_argument("--disable-sdram",  action="store_true", help="Build without onboard memory controller. (default: false)")
    parser.add_argument("--sys-clk-freq",   default=400e6,       help="System clock frequency (default: 300MHz)")
    parser.add_argument("--use-clkwiz",     action="store_true", help="Generate CRG(Clock Reset Generator) with Xilinx Clocking Wizard IP. (default: false)")
    
    builder_args(parser)
    soc_core_args(parser)
    args = parser.parse_args()

    soc = BaseSoC(
        disable_sdram = True if args.disable_sdram else False,
        sys_clk_freq = int(float(args.sys_clk_freq)),
        use_clkwiz   = args.use_clkwiz,
        **soc_core_argdict(args)
    )

    builder = LocalBuilder(soc, **builder_argdict(args))

    vns = builder.build(run=args.build)
    soc.platform.ila.generate_ila(builder.gateware_dir)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".bit"))

if __name__ == "__main__":
    main()
