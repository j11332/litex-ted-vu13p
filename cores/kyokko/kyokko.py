#!/usr/bin/env python3
from migen import *
from litex.soc.interconnect import stream
from cores.kyokko.phy.phy_usp_gty import USPGTY
import os.path

class Kyokko(Module):
    def __init__(self, platform, pads, phy, cd="sys", bond_ch = 4):
        self.user_tx_sink = stream.Endpoint([("data", 64 * bond_ch)])
        self.user_rx_source = stream.Endpoint([("data", 64 * bond_ch)])
        
        # # #
        self.cd = cd
        self.kyokko_params = dict(
            i_clk = ClockSignal(cd=self.cd),
            i_reset = ResetSignal(cd=self.cd)
        )
        
        # PHY TX
        self.kyokko_params.update(
            o_gtwiz_userdata_tx_out               = phy.tx_userdata,
            o_txheader_out                        = phy.tx_header,
            o_txsequence_out                      = phy.tx_swquence,
            i_gtwiz_reset_tx_done_in              = phy.tx_reset_done,
            i_gtwiz_userclk_tx_userclk2_in        = phy.tx_userclk,
            o_gtwiz_userclk_tx_reset_out          = phy.tx_userclk_reset,
            o_gtwiz_reset_tx_datapath_out         = phy.tx_reset_dp,
            o_gtwiz_reset_tx_pll_and_datapath_out = phy.tx_reset_dp_and_pll,
        )
        
        # PHY RX
        self.kyokko_params.update(
            i_gtwiz_userdata_rx_in                = phy.rx_data,
            i_rxheader_in                         = phy.rx_header,
            o_rxgearboxslip_out                   = phy.rx_gearbox_slip,
            i_gtwiz_reset_rx_done_in              = phy.rx_reset_done,
            i_gtwiz_userclk_rx_userclk2_in        = phy.rx_userclk,
            o_gtwiz_userclk_rx_reset_out          = phy.rx_userclk_reset,
            o_gtwiz_reset_rx_datapath_out         = phy.rx_reset_dp,
            o_gtwiz_reset_rx_pll_and_datapath_out = phy.rx_reset_dp_and_pll,
        )

        # User I/F
        self.kyokko_params.update(
            i_s_axis_tdata  = self.user_tx_sink.data,
            i_s_axis_tlast  = self.user_tx_sink.last,
            i_s_axis_tvalid = self.user_tx_sink.valid,
            o_s_axis_tready = self.user_tx_sink.ready
        )
        self.kyokko_params.update(
            o_m_axis_rx_tdata = self.user_rx_source.data,
            o_m_axis_rx_tlast = self.user_rx_source.last,
            o_m_axis_rx_tvalid = self.user_rx_source.valid,
        )
        self.comb += self.user_rx_source.ready.eq(1)
            
    @staticmethod
    def add_sources(platform):
        srcdir = os.path.join(os.path.dirname(__file__), "verilog")
        platform.add_sources(srcdir,
            "byte-reverse8.v",
            "gt-rst.v",
            "kyokko-cb.v",
            "kyokko-rx-axis.v",
            "kyokko-rx-cb.v",
            "kyokko-rx-ctrl.v",
            "kyokko-rx-init.v",
            "kyokko-tx-ctrl.v",
            "kyokko-tx-data.v",
            "kyokko-tx-init.v",
            "kyokko-tx-nfc.v",
            "kyokko-tx-ufc.v",
            "kyokko.v",
            "rxpath-rst.v",
            "teng-sc.v")
        
    def do_finalize(self):
        self.specials += [
            Instance("kyokko_cb_wrapper", **self.kyokko_params),
            Instance("gt_rst", 
                i_CLK    = ClockSignal("clk100"),
                i_RST    = ResetSignal("sys"),
                o_GT_RST = ResetSignal("clk100")
            )
        ]

