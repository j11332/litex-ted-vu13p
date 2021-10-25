#!/usr/bin/env python3
import os
import json
from migen import *
from litex.soc.interconnect import stream

class Open(Signal): pass

class Differential:
    def __init__(self, lanes):
        self.p = Signal(lanes)
        self.n = Signal.like(self.p)

class USPGTY4(Module):
    def __init__(self, platform, name, refclk, pads, cd="clk100"):
        
        # high speed serial tx/rx
        self.lanes = LANES = len(pads.tx_p)
                              
        # tx/rx datapath
        self.userdata_tx = Signal(LANES * 64)
        self.userclk_tx_usrclk2 = Signal()
        self.userclk_tx_reset = Signal()
        self.reset_tx_pll_and_datapath = Signal()
        self.reset_tx_datapath = Signal()
        self.txheader = Signal(24)
        self.reset_tx_done = Signal()
        self.txsequence = Signal(28)
        
        self.userdata_rx = Signal(LANES * 64)
        self.userclk_rx_usrclk2 = Signal()
        self.userclk_rx_reset = Signal()
        self.reset_rx_pll_and_datapath = Signal()
        self.reset_rx_datapath = Signal()
        self.rxheader = Signal(24)
        self.reset_rx_done = Signal()
        self.rxgearboxslip = Signal(4)
                
        # common
        self.reset_all = Signal()
        
        # # #
        self.name = name
        self.platform = platform
        
        # reference clock buffer
        gtrefclk = Signal()
        if isinstance(refclk, Record):
            refclk_buf = Instance(
                "IBUFDS_GTE4",
                name="refclk_buf",
                i_I = refclk.p,
                i_IB = refclk.n,
                i_CEB = 0b0,
                o_O = gtrefclk
            )
            self.specials += refclk_buf
        else:
            gtrefclk = refclk        

        self.ip_ports = dict(
            i_gtrefclk00_in = gtrefclk,
            o_gtytxn_out = pads.tx_n,
            o_gtytxp_out = pads.tx_p,
            i_gtyrxn_in  = pads.rx_n,
            i_gtyrxp_in  = pads.rx_p,
        )
        
        port_tx_dp = dict(
            i_gtwiz_userdata_tx_in = self.userdata_tx,
            o_gtwiz_userclk_tx_usrclk2_out = self.userclk_tx_usrclk2,
            i_gtwiz_userclk_tx_reset_in = self.userclk_tx_reset,
            i_gtwiz_reset_tx_pll_and_datapath_in = self.reset_tx_pll_and_datapath,
            i_gtwiz_reset_tx_datapath_in = self.reset_tx_datapath,
            i_txheader_in = self.txheader,
            o_gtwiz_reset_tx_done_out = self.reset_tx_done,
            i_txsequence_in = self.txsequence,
        )
        self.ip_ports.update(port_tx_dp)
        port_rx_dp = dict(
            o_gtwiz_userdata_rx_out = self.userdata_rx,
            o_gtwiz_userclk_rx_usrclk2_out = self.userclk_rx_usrclk2,
            i_gtwiz_userclk_rx_reset_in = self.userclk_rx_reset,
            i_gtwiz_reset_rx_pll_and_datapath_in = self.reset_rx_pll_and_datapath,
            i_gtwiz_reset_rx_datapath_in = self.reset_rx_datapath,
            o_rxheader_out = self.rxheader,
            o_gtwiz_reset_rx_done_out = self.reset_rx_done,
            i_rxgearboxslip_in = self.rxgearboxslip,
        )
        self.ip_ports.update(port_rx_dp)
  
        self.ip_ports.update(
            dict(
                i_gtwiz_reset_clk_freerun_in = ClockSignal(cd),
                i_gtwiz_reset_all_in = self.reset_all,
            )
        )
        
        self.specials += Instance("gty4", **self.ip_ports)
