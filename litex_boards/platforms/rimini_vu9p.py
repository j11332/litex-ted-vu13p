#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2020 David Shah <dave@ds0.me>
# Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

from litex.build.generic_platform import Pins, PlatformInfo, Subsignal, IOStandard, Misc
from litex.build.xilinx import XilinxPlatform, VivadoProgrammer
from litex_boards.utils import diff_clk

_io = [
    # Clk / Rst
    diff_clk("sys_clk", 0, "AY38", "AY37", iostandard = "DIFF_SSTL12", freq_hz = int(266e6)),
    diff_clk("sys_clk", 1, "AW19", "AW20", iostandard = "DIFF_SSTL12", freq_hz = int(266e6)),
    diff_clk("sys_clk", 2, "E32",  "F32",  iostandard = "DIFF_SSTL12", freq_hz = int(266e6)),
    diff_clk("sys_clk", 3, "H16",  "J16",  iostandard = "DIFF_SSTL12", freq_hz = int(266e6)),

    # PCIe bracket LEDs
    ("user_led", 0, Pins("BC21"), IOStandard("LVCMOS12")),
    ("user_led", 1, Pins("BB21"), IOStandard("LVCMOS12")),
    ("user_led", 2, Pins("BA20"), IOStandard("LVCMOS12")),

    # USB-Serial (FT4232H Port B)
    ("serial", 0,
        Subsignal("rx", Pins("BF18")),
        Subsignal("tx", Pins("BB20")),
        IOStandard("LVCMOS12"),
    ),
    
    ("qsfp", 0,
        Subsignal("rx_n", Pins("J3  H1  G3  F1")),
        Subsignal("rx_p", Pins("J4  H2  G4  F2")),
        Subsignal("tx_n", Pins("J8  H6  G8  F6")),
        Subsignal("tx_p", Pins("J9  H7  G9  F7")),
        PlatformInfo({"quad"    : "Quad_X5Y13", "channel" : ("X1Y52", "X1Y53", "X1Y54", "X1Y55")}),
    ),
    diff_clk("qsfp0_refclk", 0, "H10", "H11"),
    diff_clk("qsfp0_refclk", 1, "F10", "F11"),
    
    ("qsfp", 1,
        Subsignal("rx_n", Pins("N3  M1  L3  K1")),
        Subsignal("rx_p", Pins("N4  M2  L4  K2")),
        Subsignal("tx_n", Pins("N8  M6  L8  K6")),
        Subsignal("tx_p", Pins("N9  M7  L9  K7")),
        PlatformInfo({"quad" : "Quad_X1Y12", "channel" : ("X1Y48", "X1Y49", "X1Y50", "X1Y51")}),
    ),
    diff_clk("qsfp1_refclk", 0, "M10", "M11"),
    diff_clk("qsfp1_refclk", 1, "K10", "K11"),

    ("qsfp", 2,
        Subsignal("rx_n", Pins("U3  T1  R3  P1")),
        Subsignal("rx_p", Pins("U4  T2  R4  P2")),
        Subsignal("tx_n", Pins("U8  T6  R8  P6")),
        Subsignal("tx_p", Pins("U9  T7  R9  P7")),
        PlatformInfo({"quad" : "Quad_X1Y11", "channel" : ("X1Y44", "X1Y45", "X1Y46", "X1Y47")}),
    ),
    diff_clk("qsfp2_refclk", 0, "T10", "T11"),
    diff_clk("qsfp2_refclk", 1, "P10", "P11"),
    
    ("qsfp", 3,
        Subsignal("rx_p", Pins("AE3 AD1 AC3 AB1")), 
        Subsignal("rx_n", Pins("AE4 AD2 AC4 AB2")), 
        Subsignal("tx_p", Pins("AE8 AD6 AC8 AB6")), 
        Subsignal("tx_n", Pins("AE9 AD7 AC9 AB7")),
        PlatformInfo({"quad" : "Quad_X5Y9", "channel" : ("X1Y36", "X1Y37", "X1Y38", "X1Y39")}),
    ),
    diff_clk("qsfp3_refclk", 0, "AD10", "AD11"),
    diff_clk("qsfp3_refclk", 1, "AB10", "AB11"),

    # PCIe
    ("pcie_x2", 0,
        Subsignal("rst_n", Pins("BD21"), IOStandard("LVCMOS12")),
        Subsignal("clk_n", Pins("AM10")),
        Subsignal("clk_p", Pins("AM11")),
        Subsignal("rx_n",  Pins("AF1 AG3")),
        Subsignal("rx_p",  Pins("AF2 AG4")),
        Subsignal("tx_n",  Pins("AF6 AG8")),
        Subsignal("tx_p",  Pins("AF7 AG9")),
    ),
    ("pcie_x4", 0,
        Subsignal("rst_n", Pins("BD21"), IOStandard("LVCMOS12")),
        Subsignal("clk_n", Pins("AM10")),
        Subsignal("clk_p", Pins("AM11")),
        Subsignal("rx_n",  Pins("AF1 AG3 AH1 AJ3")),
        Subsignal("rx_p",  Pins("AF2 AG4 AH2 AJ4")),
        Subsignal("tx_n",  Pins("AF6 AG8 AH6 AJ8")),
        Subsignal("tx_p",  Pins("AF7 AG9 AH7 AJ9")),
    ),
    ("pcie_x8", 0,
        Subsignal("rst_n", Pins("BD21"), IOStandard("LVCMOS12")),
        Subsignal("clk_n", Pins("AM10")),
        Subsignal("clk_p", Pins("AM11")),
        Subsignal("rx_n",  Pins("AF1 AG3 AH1 AJ3 AK1 AL3 AM1 AN3")),
        Subsignal("rx_p",  Pins("AF2 AG4 AH2 AJ4 AK2 AL4 AM2 AN4")),
        Subsignal("tx_n",  Pins("AF6 AG8 AH6 AJ8 AK6 AL8 AM6 AN8")),
        Subsignal("tx_p",  Pins("AF7 AG9 AH7 AJ9 AK7 AL9 AM7 AN9")),
    ),
    ("pcie_x16", 0,
        Subsignal("rst_n", Pins("BD21"), IOStandard("LVCMOS12")),
        Subsignal("clk_n", Pins("AM10")),
        Subsignal("clk_p", Pins("AM11")),
        Subsignal("rx_n", Pins("AF1 AG3 AH1 AJ3 AK1 AL3 AM1 AN3 AP1 AR3 AT1 AU3 AV1 AW3 BA1 BC1")),
        Subsignal("rx_p", Pins("AF2 AG4 AH2 AJ4 AK2 AL4 AM2 AN4 AP2 AR4 AT2 AU4 AV2 AW4 BA2 BC2")),
        Subsignal("tx_n", Pins("AF6 AG8 AH6 AJ8 AK6 AL8 AM6 AN8 AP6 AR8 AT6 AU8 AV6 BB4 BD4 BF4")),
        Subsignal("tx_p", Pins("AF7 AG9 AH7 AJ9 AK7 AL9 AM7 AN9 AP7 AR9 AT7 AU9 AV7 BB5 BD5 BF5")),
    ),
]

_connectors = []

class Platform(XilinxPlatform):
    default_clk_name   = "clk300"
    default_clk_period = 1e9/300e6

    def __init__(self):
        XilinxPlatform.__init__(self, "xcvu9p-fsgd2104-3-e", _io, _connectors, toolchain="vivado")

    def create_programmer(self):
        return VivadoProgrammer()

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)
        # For passively cooled boards, overheating is a significant risk if airflow isn't sufficient
        self.add_platform_command(
            "set_property -dict { BITSTREAM.CONFIG.OVERTEMPSHUTDOWN ENABLE "
            "BITSTREAM.GENERAL.COMPRESS TRUE } [current_design]"
        )
 
        # Clock constraint
        for id in range(0, 4):
            _clk = self.lookup_request("sys_clk", id, loose=True)
            self.add_period_constraint(_clk, _clk.platform_info['freq_hz'])

        self.add_platform_command(
            "set_property INTERNAL_VREF 0.84 [get_iobanks 40]",
            "set_property INTERNAL_VREF 0.84 [get_iobanks 41]",
            "set_property INTERNAL_VREF 0.84 [get_iobanks 42]",
            "set_property INTERNAL_VREF 0.84 [get_iobanks 65]",
            "set_property INTERNAL_VREF 0.84 [get_iobanks 66]",
            "set_property INTERNAL_VREF 0.84 [get_iobanks 67]",
            "set_property INTERNAL_VREF 0.84 [get_iobanks 46]",
            "set_property INTERNAL_VREF 0.84 [get_iobanks 47]",
            "set_property INTERNAL_VREF 0.84 [get_iobanks 48]",
            "set_property INTERNAL_VREF 0.84 [get_iobanks 70]",
            "set_property INTERNAL_VREF 0.84 [get_iobanks 71]",
            "set_property INTERNAL_VREF 0.84 [get_iobanks 72]",
        )
        