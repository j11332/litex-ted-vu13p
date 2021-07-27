#!/usr/bin/env python3
import os
import json
from migen import *

class Open(Signal): pass
"""
set_property -dict [list 
    CONFIG.C_REFCLK_SOURCE_QUAD_1 {MGTREFCLK0_121} 
    CONFIG.C_REFCLK_SOURCE_QUAD_0 {MGTREFCLK0_121} 
    CONFIG.C_PROTOCOL_QUAD1 {Custom_1_/_28.021_Gbps}
    CONFIG.C_PROTOCOL_QUAD0 {Custom_1_/_28.021_Gbps} 
    CONFIG.C_GT_CORRECT {true} 
    CONFIG.C_PROTOCOL_QUAD_COUNT_1 {2} 
    CONFIG.C_PROTOCOL_REFCLK_FREQUENCY_1 {161.0402299} 
    CONFIG.C_PROTOCOL_MAXLINERATE_1 {28.021}
] [get_ips ibert_0]

"""
class IBERT(Module):
    def __init__(self, platform, name, refclks, gt_pads, clockdomain="sys"):
        self.name = name
        self.platform = platform
        
        self.ip_params = {
            "CONFIG.C_REFCLK_SOURCE_QUAD_1"         : "MGTREFCLK0_121",
            "CONFIG.C_REFCLK_SOURCE_QUAD_0"         : "MGTREFCLK0_121",
            "CONFIG.C_PROTOCOL_QUAD1"               : "Custom_1_/_28.021_Gbps",
            "CONFIG.C_PROTOCOL_QUAD0"               : "Custom_1_/_28.021_Gbps",
            "CONFIG.C_GT_CORRECT"                   : "true",
            "CONFIG.C_PROTOCOL_QUAD_COUNT_1"        : "2",
            "CONFIG.C_PROTOCOL_REFCLK_FREQUENCY_1"  : "161.0402299",
            "CONFIG.C_PROTOCOL_MAXLINERATE_1"       : "28.021",
        }

        self.clockdomain = clockdomain
        self.refclks = []
        for i, clks in enumerate(refclks):
            _bufd_clks = Signal(len(clks), reset_less=True)
            for j, clk in enumerate(clks):
                self.specials += Instance(
                    "IBUFDS_GTE4",
                    name=f"refclkbuf_quad_{i}_{j}",
                    i_I = clk.p,
                    i_IB = clk.n,
                    i_CEB = 0b0,
                    o_O = _bufd_clks[j]
                )                
            self.refclks.append(_bufd_clks)
    
        self.ip_ports = dict(
            i_clk                       = ClockSignal(cd=self.clockdomain),
            i_gtrefclk0_i               = Cat([i[0] for i in self.refclks]),
            i_gtrefclk1_i               = Cat([i[1] for i in self.refclks]),
            i_gtnorthrefclk0_i          = Cat(C(0), self.refclks[0][0]),
            i_gtnorthrefclk1_i          = Cat(C(0), self.refclks[0][1]),
            i_gtsouthrefclk0_i          = Cat(self.refclks[1][0], C(0)),
            i_gtsouthrefclk1_i          = Cat(self.refclks[1][1], C(0)),
            i_gtrefclk00_i              = Cat([i[0] for i in self.refclks]),
            i_gtrefclk01_i              = Cat([i[0] for i in self.refclks]),
            i_gtrefclk10_i              = Cat([i[1] for i in self.refclks]),
            i_gtrefclk11_i              = Cat([i[1] for i in self.refclks]),
            i_gtnorthrefclk00_i         = Cat(C(0), self.refclks[0][0]),
            i_gtnorthrefclk01_i         = Cat(C(0), self.refclks[0][0]),
            i_gtnorthrefclk10_i         = Cat(C(0), self.refclks[0][1]),
            i_gtnorthrefclk11_i         = Cat(C(0), self.refclks[0][1]),
            i_gtsouthrefclk00_i         = Cat(self.refclks[1][0], C(0)),
            i_gtsouthrefclk01_i         = Cat(self.refclks[1][0], C(0)),
            i_gtsouthrefclk10_i         = Cat(self.refclks[1][1], C(0)),
            i_gtsouthrefclk11_i         = Cat(self.refclks[1][1], C(0)),
            i_rxn_i                     = Cat([i.rxn for i in gt_pads]),
            i_rxp_i                     = Cat([i.rxp for i in gt_pads]),
            o_txn_o                     = Cat([i.txn for i in gt_pads]),
            o_txp_o                     = Cat([i.txp for i in gt_pads]),
        )
        
    def add_sources(self, path, filename):
        self.platform.add_ip(os.path.join(path, filename))

    def do_finalize(self):
        self.platform.toolchain.pre_synthesis_commands += [
            "create_ip "
            "-vlnv [get_ipdefs *ibert_ultrascale_gty*] "
            f"-module_name {self.name}"
        ]
        
        ip_params_json = json.dumps(self.ip_params)
        self.platform.toolchain.pre_synthesis_commands += [
            "set_property -quiet "
            "-dict [bd::json2dict {{"
            f"{{{ip_params_json}}}"
            "}}] "
            f"[get_ips {self.name}]"
        ]
        
        self.platform.toolchain.pre_synthesis_commands += [
            f"generate_target all [get_ips {self.name}]",
        ]
        
        self.specials.ibert_inst = Instance(self.name, **self.ip_ports, name="ibert_i")