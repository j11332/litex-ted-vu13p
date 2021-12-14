# This file is part of LiteX-Boards.
# SPDX-License-Identifier: BSD-2-Clause
from litex.build.generic_platform import *
from litex.soc.cores.clock.common import clkdiv_range
from litex_boards.xilinx import XilinxPlatform
from litex_boards.utils import diff_clk

# IOs
_io = [
    # Clk / Rst
    diff_clk("clk_200", 0, "BF22", "BE22", iostandard="DIFF_SSTL12"),
    diff_clk("clk_200", 1, "M27",  "N27",  iostandard="DIFF_SSTL12"),
    ("clk_125", 0, Pins("BD16"), IOStandard("LVCMOS18")),
    
    # GTY120 / X0Y0
    diff_clk("MGTREFCLK_120_", 0, "BD40", "BD39"), # UNIV
    diff_clk("MGTREFCLK_120_", 1, "BC42", "BC41"), # UNIV
    ("GTY120", 0,
        Subsignal("rx_n", Pins("BG33 BF35 BJ33 BH35")),
        Subsignal("rx_p", Pins("BG32 BF34 BJ32 BH34")),
        Subsignal("tx_n", Pins("BH40 BF40 BJ38 BG38")),
        Subsignal("tx_p", Pins("BH39 BF39 BJ37 BG37")),
    ),
    
    # GTY121 / X0Y1
    diff_clk("MGTREFCLK_121_", 0, "BB40", "BB39"), # Clock gen.
    diff_clk("MGTREFCLK_121_", 1, "BA42", "BA41"), # Coax.
    ("GTY121", 0,
        Subsignal("rx_n", Pins("BK35 BL33 BL47 BJ47")),
        Subsignal("rx_p", Pins("BK34 BL32 BL46 BJ46")),
        Subsignal("tx_n", Pins("BL38 BK40 BL42 BK44")),
        Subsignal("tx_p", Pins("BL37 BK39 BL41 BK43")),
        PlatformInfo({"quad" : "Quad_X0Y1", "channel" : ("X0Y4", "X0Y5", "X0Y6", "X0Y7")}),
    ),
    
    # GTY122 / X0Y2
    diff_clk("MGTREFCLK_122_", 0, "AY40", "AY39"), # UNIV
    diff_clk("MGTREFCLK_122_", 1, "AW42", "AW41"), # UNIV
    ("GTY122", 0,
        Subsignal("rx_n", Pins("BH49 BG51 BG47 BF49")),
        Subsignal("rx_p", Pins("BH48 BG50 BG46 BF48")),
        Subsignal("tx_n", Pins("BG42 BJ42 BH44 BF44")),
        Subsignal("tx_p", Pins("BG41 BJ41 BH43 BF43")),
        PlatformInfo({"quad" : "Quad_X0Y2", "channel" : ("X0Y8", "X0Y9", "X0Y10", "X0Y11")}),
    ),

    # GTY123 / X0Y3
    diff_clk("MGTREFCLK_123_", 0, "AV40", "AV39"), # Clock gen.
    diff_clk("MGTREFCLK_123_", 1, "AU42", "AU41"), # Coax.
    ("GTY", 0,
        Subsignal("rx_n", Pins("BE51 BD49 BC51 BB49")),
        Subsignal("rx_p", Pins("BE50 BD48 BC50 BB48")),
        Subsignal("tx_n", Pins("BE46 BD44 BC46 BB44")),
        Subsignal("tx_p", Pins("BE45 BD43 BC45 BB43")),
        PlatformInfo({"quad" : "Quad_X0Y3", "channel" : ("X0Y12", "X0Y13", "X0Y14", "X0Y15")}),
    ),

    # GTY124 / X0Y4
    diff_clk("MGTREFCLK_124_", 0, "AT40", "AT39"), # UNIV
    diff_clk("MGTREFCLK_124_", 1, "AR42", "AT41"), # UNIV
    ("GTY", 0,
        Subsignal("rx_n", Pins("BA51 AY49 AW51 AV49")),
        Subsignal("rx_p", Pins("BA50 AY48 AW50 AV48")),
        Subsignal("tx_n", Pins("BA46 AY44 AW46 AV44")),
        Subsignal("tx_p", Pins("BA45 AY43 AW45 AV43")),
        PlatformInfo({"quad" : "Quad_X0Y4", "channel" : ("X0Y16", "X0Y17", "X0Y18", "X0Y19")}),
    ),

    # GTY125 / X0Y5
    diff_clk("MGTREFCLK_125_", 0, "AP40", "AP39"), # Clock gen.
    diff_clk("MGTREFCLK_125_", 1, "AN42", "AN41"), # Coax.
    ("GTY", 0,
        Subsignal("rx_n", Pins("AU51 AT49 AR51 AP49")),
        Subsignal("rx_p", Pins("AU50 AT48 AR50 AP48")),
        Subsignal("tx_n", Pins("AU46 AT44 AR46 AP44")),
        Subsignal("tx_p", Pins("AU45 AT43 AR45 AP43")),
        PlatformInfo({"quad" : "Quad_X0Y5", "channel" : ("X0Y20", "X0Y21", "X0Y22", "X0Y23")}),
    ),

    # GTY126 / X0Y6
    diff_clk("MGTREFCLK_126_", 0, "AM40", "AM39"), # UNIV
    diff_clk("MGTREFCLK_126_", 1, "AL42", "AL41"), # UNIV
    ("GTY", 0,
        Subsignal("rx_n", Pins("AN51 AM49 AL51 AK49")),
        Subsignal("rx_p", Pins("AN50 AM48 AL50 AK48")),
        Subsignal("tx_n", Pins("AN46 AM44 AL46 AK44")),
        Subsignal("tx_p", Pins("AN45 AM43 AL45 AK43")),
        PlatformInfo({"quad" : "Quad_X0Y6", "channel" : ("X0Y24", "X0Y25", "X0Y26", "X0Y27")}),
    ),

    # GTY127 / X0Y7
    diff_clk("MGTREFCLK_127_", 0, "AJ42", "AJ41"), # Clock gen.
    diff_clk("MGTREFCLK_127_", 1, "AG42", "AG41"), # Coax.
    ("GTY127", 0,
        Subsignal("rx_n", Pins("AJ51 AH49 AG51 AF49")),
        Subsignal("rx_p", Pins("AJ50 AH48 AG50 AF48")),
        Subsignal("tx_n", Pins("AJ46 AH44 AG46 AF44")),
        Subsignal("tx_p", Pins("AJ45 AH43 AG45 AF43")),
        PlatformInfo({"quad" : "Quad_X0Y7", "channel" : ("X0Y28", "X0Y29", "X0Y30", "X0Y31")}),
    ),

    # GTY128 / X0Y8
    diff_clk("MGTREFCLK_128_", 0, "AE42", "AE41"), # UNIV
    diff_clk("MGTREFCLK_128_", 1, "AC42", "AC41"), # UNIV
    ("GTY128", 0,
        Subsignal("rx_n", Pins("AE51 AD49 AC51 AB49")),
        Subsignal("rx_p", Pins("AE50 AD48 AC50 AB48")),
        Subsignal("tx_n", Pins("AE46 AD44 AC45 AB43")),
        Subsignal("tx_p", Pins("AE45 AD43 AC45 AB43")),
        PlatformInfo({"quad" : "Quad_X0Y8", "channel" : ("X0Y32", "X0Y33", "X0Y34", "X0Y35")}),
    ),

    # GTY129 / X0Y9
    diff_clk("MGTREFCLK_129_", 0, "AA42", "AA41"), # Clock gen.
    diff_clk("MGTREFCLK_129_", 1, "Y40", "Y39"), # Coax.
    ("GTY129", 0,
        Subsignal("rx_n", Pins("AA51 Y49 W51 V49")),
        Subsignal("rx_p", Pins("AA50 Y48 W50 V48")),
        Subsignal("tx_n", Pins("AA46 Y44 W46 V44")),
        Subsignal("tx_p", Pins("AA45 Y43 W45 V43")),
        PlatformInfo({"quad" : "Quad_X0Y9", "channel" : ("X0Y36", "X0Y37", "X0Y38", "X0Y39")}),
    ),

    # GTY130 / X0Y10
    diff_clk("MGTREFCLK_130_", 0, "W42", "W41"), # UNIV
    diff_clk("MGTREFCLK_130_", 1, "V40", "V39"), # UNIV
    ("GTY130", 0,
        Subsignal("rx_n", Pins("U51 T49 R51 P49")),
        Subsignal("rx_p", Pins("U50 T48 R50 P48")),
        Subsignal("tx_n", Pins("U46 T44 R46 P44")),
        Subsignal("tx_p", Pins("U45 T43 R45 P43")),
        PlatformInfo({"quad" : "Quad_X0Y10", "channel" : ("X0Y40", "X0Y41", "X0Y42", "X0Y43")}),
    ),

    # GTY131 / X0Y11
    diff_clk("MGTREFCLK_131_", 0, "", ""), # Clock gen.
    diff_clk("MGTREFCLK_131_", 1, "", ""), # Coax.
    ("GTY131", 0,
        Subsignal("rx_n", Pins("")),
        Subsignal("rx_p", Pins("")),
        Subsignal("tx_n", Pins("")),
        Subsignal("tx_p", Pins("")),
        PlatformInfo({"quad" : "Quad_X0Y11", "channel" : ("X0Y44", "X0Y45", "X0Y46", "X0Y47")}),
    ),

    # GTY132 / X0Y12
    diff_clk("MGTREFCLK_132_", 0, "R42", "R41"), # UNIV
    diff_clk("MGTREFCLK_132_", 1, "P40", "P39"), # UNIV
    ("GTY132", 0,
        Subsignal("rx_n", Pins("J51 H49 G51 F49")),
        Subsignal("rx_p", Pins("J50 H48 G50 F48")),
        Subsignal("tx_n", Pins("J46 H43 G45 F43")),
        Subsignal("tx_p", Pins("J45 H43 G45 F43")),
        PlatformInfo({"quad" : "Quad_X0Y12", "channel" : ("X0Y48", "X0Y49", "X0Y50", "X0Y51")}),
    ),

    # GTY133 / X0Y13
    diff_clk("MGTREFCLK_133_", 0, "N42", "N41"), # Clock gen.
    diff_clk("MGTREFCLK_133_", 1, "M40", "M39"), # Coax.
    ("GTY133", 0,
        Subsignal("rx_n", Pins("E51 D49 E47 C47")),
        Subsignal("rx_p", Pins("E50 D48 E46 C46")),
        Subsignal("tx_n", Pins("D44 B44 C42 E42")),
        Subsignal("tx_p", Pins("D43 B43 C41 E41")),
        PlatformInfo({"quad" : "Quad_X0Y13", "channel" : ("X0Y52", "X0Y53", "X0Y54", "X0Y55")}),
    ),

    # GTY134 / X0Y14
    diff_clk("MGTREFCLK_134_", 0, "L42", "L41"), # UNIV
    diff_clk("MGTREFCLK_134_", 1, "K40", "K39"), # UNIV
    ("GTY134", 0,
        Subsignal("rx_n", Pins("A47 A33 B35 C33")),
        Subsignal("rx_p", Pins("A46 A32 B34 C32")),
        Subsignal("tx_n", Pins("A42 B40 A38 C38")),
        Subsignal("tx_p", Pins("A41 B39 A37 C37")),
        PlatformInfo({"quad" : "Quad_X0Y14", "channel" : ("X0Y56", "X0Y57", "X0Y58", "X0Y59")}),
    ),

    # GTY135 / X0Y15
    diff_clk("MGTREFCLK_135_", 0, "J42", "J41"), # Clock gen.
    diff_clk("MGTREFCLK_135_", 1, "H40", "H39"), # Coax.
    ("GTY135", 0,
        Subsignal("rx_n", Pins("D35 E33 F35 G33")),
        Subsignal("rx_p", Pins("D34 E32 F34 G32")),
        Subsignal("tx_n", Pins("D40 E38 F40 G38")),
        Subsignal("tx_p", Pins("D39 E37 F39 G37")),
        PlatformInfo({"quad" : "Quad_X0Y15", "channel" : ("X0Y60", "X0Y61", "X0Y62", "X0Y63")}),
    ),

    # GTY220 / X1Y0
    diff_clk("MGTREFCLK_220_", 0, "BD12", "BD13"), # UNIV
    diff_clk("MGTREFCLK_220_", 1, "BC10", "BC11"), # UNIV
    ("GTY220", 0,
        Subsignal("rx_n", Pins("BG19 BF17 BJ19 BH17")),
        Subsignal("rx_p", Pins("BG20 BF18 BJ20 BH18")),
        Subsignal("tx_n", Pins("BH12 BF12 BJ14 BG14")),
        Subsignal("tx_p", Pins("BH13 BF13 BJ15 BG15")),
        PlatformInfo({"quad" : "Quad_X1Y0", "channel" : ("X1Y0", "X1Y1", "X1Y2", "X1Y3")}),
    ),

    # GTY221 / X1Y1
    diff_clk("MGTREFCLK_221_", 0, "BB12", "BB13"), # Clock gen.
    diff_clk("MGTREFCLK_221_", 1, "BA10", "BA11"), # Coax.
    ("GTY221", 0,
        Subsignal("rx_n", Pins("BK17 BL19 BL5 BJ5")),
        Subsignal("rx_p", Pins("BK18 BL20 BL6 BJ6")),
        Subsignal("tx_n", Pins("BL14 BK12 BL10 BK8")),
        Subsignal("tx_p", Pins("BL15 BK13 BL11 BK9")),
        PlatformInfo({"quad" : "Quad_X1Y1", "channel" : ("X1Y4", "X1Y5", "X1Y6", "X1Y7")}),
    ),

    # GTY222 / X1Y2
    diff_clk("MGTREFCLK_222_", 0, "AY12", "AY13"), # UNIV
    diff_clk("MGTREFCLK_222_", 1, "AW10", "AW11"), # UNIV
    ("GTY222", 0,
        Subsignal("rx_n", Pins("BH3 BG1 BG5 BF3")),
        Subsignal("rx_p", Pins("BH4 BG2 BG6 BF4")),
        Subsignal("tx_n", Pins("BG10 BJ10 BH8 BF8")),
        Subsignal("tx_p", Pins("BG11 BJ11 BH9 BF9")),
        PlatformInfo({"quad" : "Quad_X1Y2", "channel" : ("X1Y8", "X1Y9", "X1Y10", "X1Y11")}),
    ),

    # GTY223 / X1Y3
    diff_clk("MGTREFCLK_223_", 0, "AV12", "AV13"), # Clock gen.
    diff_clk("MGTREFCLK_223_", 1, "AU10", "AU11"), # Coax.
    ("GTY223", 0,
        Subsignal("rx_n", Pins("BE1 BD3 BC1 BB3")),
        Subsignal("rx_p", Pins("BE2 BD4 BC2 BB4")),
        Subsignal("tx_n", Pins("BE6 BD8 BC6 BB8")),
        Subsignal("tx_p", Pins("BE7 BD9 BC7 BB9")),
        PlatformInfo({"quad" : "Quad_X1Y3", "channel" : ("X1Y12", "X1Y13", "X1Y14", "X1Y15")}),
    ),

    # TODO : GTY224-227 for PCIe

    # GTY228 / X1Y8
    diff_clk("MGTREFCLK_228_", 0, "AE10", "AE11"), # UNIV
    diff_clk("MGTREFCLK_228_", 1, "AC10", "AC11"), # UNIV
    ("GTY228", 0,
        Subsignal("rx_n", Pins("AE1 AD3 AC1 AB3")),
        Subsignal("rx_p", Pins("AE2 AD4 AC2 AB4")),
        Subsignal("tx_n", Pins("AE6 AD8 AC6 AB8")),
        Subsignal("tx_p", Pins("AE7 AD9 AC7 AB9")),
        PlatformInfo({"quad" : "Quad_X1Y8", "channel" : ("X1Y32", "X1Y33", "X1Y34", "X1Y35")}),
    ),

    # GTY229 / X1Y9
    diff_clk("MGTREFCLK_229_", 0, "AA10", "AA11"), # Clock gen.
    diff_clk("MGTREFCLK_229_", 1, "Y12", "Y13"), # Coax.
    ("GTY229", 0,
        Subsignal("rx_n", Pins("AA1 Y3 W1 V3")),
        Subsignal("rx_p", Pins("AA2 Y4 W2 V4")),
        Subsignal("tx_n", Pins("AA6 Y8 W6 V8")),
        Subsignal("tx_p", Pins("AA7 Y9 W7 V9")),
        PlatformInfo({"quad" : "Quad_X1Y9", "channel" : ("X1Y36", "X1Y37", "X1Y38", "X1Y39")}),
    ),

    # GTY230 / X1Y10
    diff_clk("MGTREFCLK_230_", 0, "W10", "W11"), # UNIV
    diff_clk("MGTREFCLK_230_", 1, "V12", "V13"), # UNIV
    ("GTY230", 0,
        Subsignal("rx_n", Pins("U1 T3 R1 P3")),
        Subsignal("rx_p", Pins("U2 T4 R2 P4")),
        Subsignal("tx_n", Pins("U6 T8 R6 P8")),
        Subsignal("tx_p", Pins("U7 T9 R7 P9")),
        PlatformInfo({"quad" : "Quad_X1Y10", "channel" : ("X1Y40", "X1Y41", "X1Y42", "X1Y43")}),
    ),

    # GTY231 / X1Y11
    diff_clk("MGTREFCLK_231_", 0, "U10", "U11"), # Clock gen.
    diff_clk("MGTREFCLK_231_", 1, "T12", "T13"), # Coax.
    ("GTY231", 0,
        Subsignal("rx_n", Pins("N1 M3 L1 K3")),
        Subsignal("rx_p", Pins("N2 M4 L2 K4")),
        Subsignal("tx_n", Pins("N6 M8 L6 K8")),
        Subsignal("tx_p", Pins("N7 M9 L7 K9")),
        PlatformInfo({"quad" : "Quad_X1Y11", "channel" : ("X1Y44", "X1Y45", "X1Y46", "X1Y47")}),
    ),

    # GTY232 / X1Y12
    diff_clk("MGTREFCLK_232_", 0, "R10", "R11"), # UNIV
    diff_clk("MGTREFCLK_232_", 1, "P12", "P13"), # UNIV
    ("GTY232", 0,
        Subsignal("rx_n", Pins("J1 H3 G1 F3")),
        Subsignal("rx_p", Pins("J2 H4 G2 F4")),
        Subsignal("tx_n", Pins("J6 H8 G6 F8")),
        Subsignal("tx_p", Pins("J7 H9 G7 F9")),
        PlatformInfo({"quad" : "Quad_X1Y12", "channel" : ("X1Y48", "X1Y49", "X1Y50", "X1Y51")}),
    ),

    # GTY233 / X1Y13
    diff_clk("MGTREFCLK_233_", 0, "N10", "N11"), # Clock gen.
    diff_clk("MGTREFCLK_233_", 1, "M12", "M13"), # Coax.
    ("GTY233", 0,
        Subsignal("rx_n", Pins("E1 D3 E5 C5")),
        Subsignal("rx_p", Pins("E2 D4 E6 C6")),
        Subsignal("tx_n", Pins("D8 B8 C10 E10")),
        Subsignal("tx_p", Pins("D9 B9 C11 E11")),
        PlatformInfo({"quad" : "Quad_X1Y13", "channel" : ("X1Y52", "X1Y53", "X1Y54", "X1Y55")}),
    ),

    # GTY234 / X1Y14
    diff_clk("MGTREFCLK_234_", 0, "L10", "L11"), # UNIV
    diff_clk("MGTREFCLK_234_", 1, "K12", "K13"), # UNIV
    ("GTY234", 0,
        Subsignal("rx_n", Pins("A5 A19 B17 C19")),
        Subsignal("rx_p", Pins("A6 A20 B18 C20")),
        Subsignal("tx_n", Pins("A10 B12 A14 C14")),
        Subsignal("tx_p", Pins("A11 B13 A15 C15")),
        PlatformInfo({"quad" : "Quad_X1Y14", "channel" : ("X1Y56", "X1Y57", "X1Y58", "X1Y59")}),
    ),

    # GTY / X1Y15
    diff_clk("MGTREFCLK_235_", 0, "J10", "J11"), # Clock gen.
    diff_clk("MGTREFCLK_235_", 1, "H12", "H13"), # Coax.
    ("GTY235", 0,
        Subsignal("rx_n", Pins("D17 E19 F17 G19")),
        Subsignal("rx_p", Pins("D18 E20 F18 G20")),
        Subsignal("tx_n", Pins("D12 E14 F12 G14")),
        Subsignal("tx_p", Pins("D13 E15 F13 G15")),
        PlatformInfo({"quad" : "Quad_X1Y15", "channel" : ("X1Y60", "X1Y61", "X1Y62", "X1Y63")}),
    ),
    
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
    ("i2c_si5341", 0,
        Subsignal("sda", Pins("AW20"),  IOStandard("LVCMOS18")),
        Subsignal("scl", Pins("AW19"),  IOStandard("LVCMOS18"))
    ),
    ("i2c_si5341", 1,
        Subsignal("sda", Pins("AT20"),  IOStandard("LVCMOS18")),
        Subsignal("scl", Pins("AT19"),  IOStandard("LVCMOS18"))
    ),

    ("tca9548_reset_n", 3, Pins("BB21"), IOStandard("LVCMOS18")),
    ("tca9548_reset_n", 2, Pins("BD20"), IOStandard("LVCMOS18")),
    ("tca9548_reset_n", 1, Pins("AY21"), IOStandard("LVCMOS18")),
    ("tca9548_reset_n", 0, Pins("AY20"), IOStandard("LVCMOS18")),
    ("si5341_in_sel_0", 1, Pins("BA19"), IOStandard("LVCMOS18")),
    ("si5341_in_sel_0", 0, Pins("BA18"), IOStandard("LVCMOS18")),
    ("si5341_syncb", 1, Pins("BC19"), IOStandard("LVCMOS18")),
    ("si5341_syncb", 0, Pins("BC18"), IOStandard("LVCMOS18")),
    ("si5341_lolb", 1, Pins("AU21"), IOStandard("LVCMOS18")),
    ("si5341_lolb", 0, Pins("AU19"), IOStandard("LVCMOS18")),
    ("si5341_rstb", 1, Pins("AU22"), IOStandard("LVCMOS18")),
    ("si5341_rstb", 0, Pins("AU20"), IOStandard("LVCMOS18")),

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
    default_clk_name        = ("clk_200", 0)
    _default_clk_freq_f      = 200e6
    default_clk_freq        = int(_default_clk_freq_f)
    default_clk_period_ns   = (1e9/_default_clk_freq_f)
    part                    = "xcvu13p-flga2577-2-e"
    
    def __init__(self):
        XilinxPlatform.__init__(self, self.part, _io, _connectors, toolchain="vivado")
        self.set_ip_cache_dir("./tmp/ip_cache")
        import util.xilinx_ila
        self.ila = util.xilinx_ila.XilinxILATracer(self)

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)
        for _id in range(0, 2):
            self.add_period_constraint(self.lookup_request("clk_200", _id, loose=True), 1e9/200e6)
            
        self.add_period_constraint(self.lookup_request("clk_125", loose=True), 1e9/125e6)

        self.add_platform_command(
            "set_property -dict {{ "
                "CONFIG_VOLTAGE 1.8 "
                "CFGBVS GND "
                "BITSTREAM.CONFIG.EXTMASTERCCLK_EN DIV-1 "
                "BITSTREAM.CONFIG.CONFIGRATE 31.9 "
                "BITSTREAM.CONFIG.SPI_32BIT_ADDR YES "
                "BITSTREAM.CONFIG.SPI_BUSWIDTH 8 "
                "BITSTREAM.GENERAL.COMPRESS TRUE "
                "BITSTREAM.CONFIG.SPI_FALL_EDGE YES"
            " }} [current_design]"
        )

        # DDR4 memory channel C1, C2 Internal Vref
        for bank in ["61", "62", "63", "73", "74", "75"]:
            self.add_platform_command(
                f"set_property INTERNAL_VREF 0.84 [get_iobanks {bank}]"
            )
        
        # FIXME: Apply before opt_design
        self.add_platform_command(
            "set_property -quiet CLOCK_DEDICATED_ROUTE FALSE [get_nets clk_125_IBUF_inst/O]")