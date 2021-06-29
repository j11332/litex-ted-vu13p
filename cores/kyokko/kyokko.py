#!/usr/bin/env python3
from migen import *
from litex.soc.interconnect import stream
class Kyokko(Module):
    def __init__(self, pads, bond_ch = 4):
        self.user_tx_sink = stream.Endpoint([("data", 64 * bond_ch)])
        self.user_rx_source = stream.Endpoint([("data", 64 * bond_ch)])
        self.pads = pads
        # # #
        self.kyokko_params = dict(
            p_BondingCh = bond_ch,
            i_CLK = Signal,
            i_CLK100 = ClockSignal("sys"),
        )
        
        