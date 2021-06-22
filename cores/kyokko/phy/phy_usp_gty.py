#!/usr/bin/env python3
import os
import json
from migen import *

class USPGTY(Module):
    def __init__(self, platform, name):
        self.name = name
        self.platform = platform
        self.ip_params = {
            "CONFIG.CHANNEL_ENABLE" : "X0Y0 X0Y1 X0Y2 X0Y3",
            "CONFIG.FREERUN_FREQUENCY"  : "100",
            "CONFIG.LOCATE_RX_USER_CLOCKING"    : "CORE",
            "CONFIG.LOCATE_TX_USER_CLOCKING"    : "CORE",
            "CONFIG.PRESET" : "GTY-Aurora_64B66B",
            "CONFIG.RX_CB_MAX_LEVEL"    : "2",
            "CONFIG.RX_DATA_DECODING"   : "64B66B_ASYNC",
            "CONFIG.RX_JTOL_FC" : "10",
            "CONFIG.RX_LINE_RATE"   : "25.78125",
            "CONFIG.RX_MASTER_CHANNEL"  : "X0Y0",
            "CONFIG.RX_OUTCLK_SOURCE"   : "RXPROGDIVCLK",
            "CONFIG.RX_REFCLK_FREQUENCY"    : "161.1328125",
            "CONFIG.TXPROGDIV_FREQ_VAL" : "390.625",
            "CONFIG.TX_DATA_ENCODING"   : "64B66B_ASYNC",
            "CONFIG.TX_LINE_RATE"   : "25.78125",
            "CONFIG.TX_MASTER_CHANNEL"  : "X0Y0",
            "CONFIG.TX_OUTCLK_SOURCE"   : "TXPROGDIVCLK",
            "CONFIG.TX_REFCLK_FREQUENCY"    : "161.1328125"
        }

    def add_sources(self, path, filename):
        self.platform.add_ip(os.path.join(path, filename))

    def do_finalize(self):
        self.platform.toolchain.pre_synthesis_commands += [
            "create_ip "
            "-vlnv [get_ipdefs *gtwizard_ultrascale*] "
            f"-module_name {self.name}"
        ]
        
        ip_params_json = json.dumps(self.ip_params)
        self.platform.toolchain.pre_synthesis_commands += [
            "set_property "
            "-dict [bd::json2dict {{"
            f"{{{ip_params_json}}}"
            "}}] "
            f"[get_ips {self.name}]"
        ]

