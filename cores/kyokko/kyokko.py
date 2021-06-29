#!/usr/bin/env python3
from migen import *
from litex.soc.interconnect import stream
from cores.kyokko.phy.phy_usp_gty import USPGTY
import os.path

def _ky_phy_layout(bond_ch):
    return [
        ("RXCLK",       bond_ch),
        ("TXCLK",       bond_ch),
        ("RXRST",       bond_ch),
        ("TXRST",       bond_ch),
        ("CH_UP",       1),
        ("RXHDR",       bond_ch * 2),
        ("RXS",         bond_ch * 64),
        ("RXSLIP",      bond_ch),
        ("RXPATH_RST",  bond_ch),
        ("TXHDR",       bond_ch * 2),
        ("TXS",         bond_ch * 64)
    ]

class Kyokko(Module):
    def __init__(self, platform, pads, bond_ch = 4):
        self.user_tx_sink = stream.Endpoint([("data", 64 * bond_ch)])
        self.user_rx_source = stream.Endpoint([("data", 64 * bond_ch)])
        self.ufc_msg = stream.Endpoint([("msg", 8)])
        self.ufc_tx_sink = stream.Endpoint([("data", 64 * bond_ch)])
        self.ufc_rx_source = stream.Endpoint([("data", 64 * bond_ch)])
        self.nfc_tx_sink = stream.Endpoint([("data", 16)])
        
        # # #
        phy_if = Record(_ky_phy_layout(bond_ch))
        self.kyokko_params = dict(
            p_BondingCh = bond_ch,
            i_CLK = Signal(),
            i_CLK100 = ClockSignal("sys"),
            i_RXCLK = phy_if.RXCLK,
            i_TXCLK = phy_if.TXCLK,
            i_RXRST = phy_if.RXRST,
            i_TXRST = phy_if.TXRST,
            o_CH_UP = phy_if.CH_UP,
            i_RXHDR = phy_if.RXHDR,
            i_RXS = phy_if.RXS,
            o_RXSLIP = phy_if.RXSLIP,
            o_RXPATH_RST = phy_if.RXPATH_RST,
            o_TXHDR = phy_if.TXHDR,
            o_TXS = phy_if.TXS
        )

        # TX User I/F
        self.kyokko_params.update(
            i_S_AXIS_TVALID = self.user_tx_sink.valid,
            i_S_AXIS_TLAST = self.user_tx_sink.last,
            i_S_AXIS_TDATA = self.user_tx_sink.data,
            o_S_AXIS_TREADY = self.user_tx_sink.ready
        )

        # RX User I/F
        self.kyokko_params.update(
            o_M_AXIS_TVALID = self.user_rx_source.valid,
            o_M_AXIS_TLAST = self.user_rx_source.last,
            o_M_AXIS_TDATA = self.user_rx_source.data
        )
        self.comb += self.user_rx_source.ready.eq(1)


        # TX UFC I/F
        self.kyokko_params.update(
            i_S_AXIS_UFC_TVALID = self.ufc_tx_sink.valid,
            i_S_AXIS_UFC_TDATA = self.ufc_tx_sink.data,
            o_S_AXIS_UFC_TREADY = self.ufc_tx_sink.ready
        )

        # RX UFC I/F
        self.kyokko_params.update(
            o_M_AXIS_UFC_TVALID = self.ufc_rx_source.valid,
            o_M_AXIS_UFC_TLAST = self.ufc_rx_source.last,
            o_M_AXIS_UFC_TDATA = self.ufc_rx_source.data
        )
        self.comb += self.ufc_rx_source.ready.eq(1)

        self.kyokko_params.update(
            i_UFC_REQ = self.ufc_msg.valid,
            i_UFC_MS = self.ufc_msg.msg
        )

        # NFC
        self.kyokko_params.update(
            i_S_AXIS_NFC_TVALID = self.nfc_tx_sink.valid,
            i_S_AXIS_NFC_TDATA = self.nfc_tx_sink.data,
            o_S_AXIS_NFC_TREADY = self.nfc_tx_sink.ready
        )
        print(pads)
        self.submodules.phy = USPGTY(platform, "phy", pads, phy_if)
    
    def do_finalize(self):
        self.specials += Instance("kyokko-cb", **self.kyokko_params)
        # srcdir = os.path.join(os.path.dirname(__file__), "rtl")
        # platform.add_sources(srcdir, "kyokko-cb.sv")

