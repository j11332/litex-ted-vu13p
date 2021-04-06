# This file is part of LiteX-Boards.
# SPDX-License-Identifier: BSD-2-Clause
from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform, VivadoProgrammer

# IOs
_io = [
    # Clk / Rst
    ("sys_clk_0", 0,
        Subsignal("p", Pins("BE22"), IOStandard("DIFF_SSTL12")),
        Subsignal("n", Pins("BF22"), IOStandard("DIFF_SSTL12")),
    ),
    ("sys_clk_1", 0,
        Subsignal("p", Pins("N27"), IOStandard("DIFF_SSTL12")),
        Subsignal("n", Pins("M27"), IOStandard("DIFF_SSTL12")),
    ),
    ("clk125", 0, Pins("BD16"), IOStandard("LVCMOS18")),
    
    # PSW[0] - Active-low
    ("cpu_resetn", 0, Pins("P36"), IOStandard("LVCMOS12")),

    # Leds
    ("user_led", 7, Pins("AW15"), IOStandard("LVCMOS18")),
    ("user_led", 6, Pins("AV16"), IOStandard("LVCMOS18")),
    ("user_led", 5, Pins("BA15"), IOStandard("LVCMOS18")),
    ("user_led", 4, Pins("AY15"), IOStandard("LVCMOS18")),
    ("user_led", 3, Pins("AV17"), IOStandard("LVCMOS18")),
    ("user_led", 2, Pins("AU17"), IOStandard("LVCMOS18")),
    ("user_led", 1, Pins("AY16"), IOStandard("LVCMOS18")),
    ("user_led", 0, Pins("AW16"), IOStandard("LVCMOS18")),

    # Serial
    ("serial", 0,
        Subsignal("rx",  Pins("C30"), IOStandard("LVCMOS18")),
        Subsignal("tx",  Pins("C29"), IOStandard("LVCMOS18")),
    ),

    # I2C
    ("i2c_tca9548", 0, 
        Subsignal("sda", Pins("BD21"), IOStandard("LVCMOS18")),
        Subsignal("scl", Pins("BA20"), IOStandard("LVCMOS18"))
    ),
    ("i2c_tca9548", 1, 
        Subsignal("sda", Pins("BB19"), IOStandard("LVCMOS18")),
        Subsignal("scl", Pins("BB20"), IOStandard("LVCMOS18"))
    ),
    ("i2c_tca9548", 2, 
        Subsignal("sda", Pins("AW21"), IOStandard("LVCMOS18")),
        Subsignal("scl", Pins("BD19"), IOStandard("LVCMOS18"))
    ),
    ("i2c_tca9548", 3, 
        Subsignal("sda", Pins("AY22"), IOStandard("LVCMOS18")),
        Subsignal("scl", Pins("BC21"), IOStandard("LVCMOS18"))
    ),
    ("i2c_tca9555", 0, 
        Subsignal("sda", Pins("A30"),  IOStandard("LVCMOS18")),
        Subsignal("scl", Pins("A28"),  IOStandard("LVCMOS18"))
    ),
    ("i2c_tca9555", 1, 
        Subsignal("sda", Pins("C28"),  IOStandard("LVCMOS18")),
        Subsignal("scl", Pins("B29"),  IOStandard("LVCMOS18"))
    ),
    ("i2c_tca9555", 2, 
        Subsignal("sda", Pins("D29"),  IOStandard("LVCMOS18")),
        Subsignal("scl", Pins("E30"),  IOStandard("LVCMOS18"))
    ),
    ("i2c_tca9555", 3, 
        Subsignal("sda", Pins("F28"),  IOStandard("LVCMOS18")),
        Subsignal("scl", Pins("F29"),  IOStandard("LVCMOS18"))
    ),
    ("i2c_tca9555", 4, 
        Subsignal("sda", Pins("G29"),  IOStandard("LVCMOS18")),
        Subsignal("scl", Pins("G30"),  IOStandard("LVCMOS18"))
    ),
    ("i2c_tca9555", 5, 
        Subsignal("sda", Pins("K30"),  IOStandard("LVCMOS18")),
        Subsignal("scl", Pins("J30"),  IOStandard("LVCMOS18"))
    ),
    ("i2c_tca9555", 6, 
        Subsignal("sda", Pins("J31"),  IOStandard("LVCMOS18")),
        Subsignal("scl", Pins("J29"),  IOStandard("LVCMOS18"))
    ),

    ("tca9548_reset_n", 3, Pins("BB21"), IOStandard("LVCMOS18")),
    ("tca9548_reset_n", 2, Pins("BD20"), IOStandard("LVCMOS18")),
    ("tca9548_reset_n", 1, Pins("AY21"), IOStandard("LVCMOS18")),
    ("tca9548_reset_n", 0, Pins("AY20"), IOStandard("LVCMOS18")),
    # DDR4 memory channel C0. Only use the first 64 data bits
    ("ddram", 0,
        Subsignal("a", Pins(
            "BE25 AW23 BC23 AY23 BC24 BD23 BB24 BE23",
            "BE20 BC22 AY25 BF25 BE21 BA27"),
            IOStandard("SSTL12_DCI")),
        Subsignal("ba",        Pins("BB25 BA25"), IOStandard("SSTL12_DCI")),
        Subsignal("bg",        Pins("BA23 BD24"), IOStandard("SSTL12_DCI")),
        Subsignal("ras_n",     Pins("BD26"), IOStandard("SSTL12_DCI")), # A16
        Subsignal("cas_n",     Pins("BB26"), IOStandard("SSTL12_DCI")), # A15
        Subsignal("we_n",      Pins("AW24"), IOStandard("SSTL12_DCI")), # A14
        Subsignal("cs_n",      Pins("BC26"), IOStandard("SSTL12_DCI")),
        Subsignal("act_n",     Pins("BA24"), IOStandard("SSTL12_DCI")),
        Subsignal("dm",        Pins(
            "BL24 BH28 BG26 BC28 BA28 BE31 BD35 AW35"), IOStandard("POD12_DCI")),
        Subsignal("dq",        Pins(
            "BK25 BL25 BH24 BH23 BK22 BL22 BJ25 BJ24",
            "BK30 BL30 BJ26 BK26 BL27 BL28 BJ29 BJ30",
            "BF27 BF28 BE26 BE27 BF29 BG30 BG29 BH29",
            "BB31 BC31 BB29 BC29 BD28 BE28 BD30 BE30",
            "AV29 AW29 AW31 AY31 AW28 AY28 AY30 BA30",
            "BC33 BD33 BC34 BD34 BB32 BC32 AY32 BA32",
            "BA35 BB35 BA34 BB34 BC37 BD37 BA37 BB37",
            "AW33 AW34 AU34 AV34 AY35 AY36 AV36 AV37"),
            IOStandard("POD12_DCI"),
            Misc("PRE_EMPHASIS=RDRV_240"),
            Misc("EQUALIZATION=EQ_LEVEL2")),
        Subsignal("dqs_p",      Pins(
            "BJ23 BK27 BH26 BB27 AU31 AY33 BB36 AV32"),
		    IOStandard("DIFF_POD12"),
            Misc("PRE_EMPHASIS=RDRV_240"),
            Misc("EQUALIZATION=EQ_LEVEL2")),
        Subsignal("dqs_n",   Pins(
            "BK23 BK28 BH27 BC27 AV31 BA33 BC36 AV33"),
		    IOStandard("DIFF_POD12"),
            Misc("PRE_EMPHASIS=RDRV_240"),
            Misc("EQUALIZATION=EQ_LEVEL2")),
        Subsignal("clk_p",   Pins("BG25"), IOStandard("DIFF_SSTL12_DCI")),
        Subsignal("clk_n",   Pins("BG24"), IOStandard("DIFF_SSTL12_DCI")),
        Subsignal("cke",     Pins("BB22"), IOStandard("SSTL12_DCI")),
        Subsignal("odt",     Pins("AW25"), IOStandard("SSTL12_DCI")),
        Subsignal("reset_n", Pins("AV26"), IOStandard("LVCMOS12")),
        Misc("SLEW=FAST"),
    ),
]

# Connectors
_connectors = []

# Platform
class Platform(XilinxPlatform):
    default_clk_name   = "sys_clk_0"
    default_clk_period = 1e9/200e6

    def __init__(self):
        XilinxPlatform.__init__(self, "xcvu13p-flga2577-2-e", _io, _connectors, toolchain="vivado")

    def create_programmer(self):
        return VivadoProgrammer()

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("sys_clk_0", loose=True), 1e9/200e6)
        self.add_period_constraint(self.lookup_request("sys_clk_1", loose=True), 1e9/200e6)
        self.add_period_constraint(self.lookup_request("clk125",    loose=True), 1e9/125e6)

        self.add_platform_command("set_property CONFIG_VOLTAGE 1.8                      [current_design]")
        self.add_platform_command("set_property CFGBVS GND                              [current_design]")
        self.add_platform_command("set_property BITSTREAM.CONFIG.EXTMASTERCCLK_EN DIV-1 [current_design]")
        self.add_platform_command("set_property BITSTREAM.CONFIG.CONFIGRATE 31.9        [current_design]")
        self.add_platform_command("set_property BITSTREAM.CONFIG.SPI_32BIT_ADDR YES     [current_design]")
        self.add_platform_command("set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 8         [current_design]")
        self.add_platform_command("set_property BITSTREAM.GENERAL.COMPRESS TRUE         [current_design]")
        self.add_platform_command("set_property BITSTREAM.CONFIG.SPI_FALL_EDGE YES      [current_design]")

        # DDR4 memory channel C1 Internal Vref
        self.add_platform_command("set_property INTERNAL_VREF 0.84 [get_iobanks 61]")
        self.add_platform_command("set_property INTERNAL_VREF 0.84 [get_iobanks 62]")
        self.add_platform_command("set_property INTERNAL_VREF 0.84 [get_iobanks 63]")

        # DDR4 memory channel C2 Internal Vref
        self.add_platform_command("set_property INTERNAL_VREF 0.84 [get_iobanks 73]")
        self.add_platform_command("set_property INTERNAL_VREF 0.84 [get_iobanks 74]")
        self.add_platform_command("set_property INTERNAL_VREF 0.84 [get_iobanks 75]")