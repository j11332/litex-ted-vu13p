#!/usr/bin/env python3
import os
import json
from migen import *

"""
i_gtwiz_userclk_tx_reset_in    #input wire [0 : 0] gtwiz_userclk_tx_reset_in;
o_gtwiz_userclk_tx_srcclk_out #output wire [0 : 0] gtwiz_userclk_tx_srcclk_out;
o_gtwiz_userclk_tx_usrclk_out #output wire [0 : 0] gtwiz_userclk_tx_usrclk_out;
o_gtwiz_userclk_tx_usrclk2_out    #output wire [0 : 0] gtwiz_userclk_tx_usrclk2_out;
o_gtwiz_userclk_tx_active_out #output wire [0 : 0] gtwiz_userclk_tx_active_out;
i_gtwiz_userclk_rx_reset_in    #input wire [0 : 0] gtwiz_userclk_rx_reset_in;
o_gtwiz_userclk_rx_srcclk_out #output wire [0 : 0] gtwiz_userclk_rx_srcclk_out;
o_gtwiz_userclk_rx_usrclk_out #output wire [0 : 0] gtwiz_userclk_rx_usrclk_out;
o_gtwiz_userclk_rx_usrclk2_out    #output wire [0 : 0] gtwiz_userclk_rx_usrclk2_out;
o_gtwiz_userclk_rx_active_out #output wire [0 : 0] gtwiz_userclk_rx_active_out;
i_gtwiz_reset_clk_freerun_in   #input wire [0 : 0] gtwiz_reset_clk_freerun_in;
i_gtwiz_reset_all_in   #input wire [0 : 0] gtwiz_reset_all_in;
i_gtwiz_reset_tx_pll_and_datapath_in   #input wire [0 : 0] gtwiz_reset_tx_pll_and_datapath_in;
i_gtwiz_reset_tx_datapath_in   #input wire [0 : 0] gtwiz_reset_tx_datapath_in;
i_gtwiz_reset_rx_pll_and_datapath_in   #input wire [0 : 0] gtwiz_reset_rx_pll_and_datapath_in;
i_gtwiz_reset_rx_datapath_in   #input wire [0 : 0] gtwiz_reset_rx_datapath_in;
o_gtwiz_reset_rx_cdr_stable_out   #output wire [0 : 0] gtwiz_reset_rx_cdr_stable_out;
o_gtwiz_reset_tx_done_out #output wire [0 : 0] gtwiz_reset_tx_done_out;
o_gtwiz_reset_rx_done_out #output wire [0 : 0] gtwiz_reset_rx_done_out;
i_gtwiz_userdata_tx_in   #input wire [255 : 0] gtwiz_userdata_tx_in;
o_gtwiz_userdata_rx_out #output wire [255 : 0] gtwiz_userdata_rx_out;
i_gtrefclk00_in    #input wire [0 : 0] gtrefclk00_in;
o_qpll0outclk_out #output wire [0 : 0] qpll0outclk_out;
o_qpll0outrefclk_out  #output wire [0 : 0] qpll0outrefclk_out;
i_gtyrxn_in    #input wire [3 : 0] gtyrxn_in;
i_gtyrxp_in    #input wire [3 : 0] gtyrxp_in;
i_rxgearboxslip_in #input wire [3 : 0] rxgearboxslip_in;
i_txheader_in #input wire [23 : 0] txheader_in;
i_txsequence_in   #input wire [27 : 0] txsequence_in;
o_gtpowergood_out #output wire [3 : 0] gtpowergood_out;
o_gtytxn_out  #output wire [3 : 0] gtytxn_out;
o_gtytxp_out  #output wire [3 : 0] gtytxp_out;
o_rxdatavalid_out #output wire [7 : 0] rxdatavalid_out;
o_rxheader_out   #output wire [23 : 0] rxheader_out;
o_rxheadervalid_out   #output wire [7 : 0] rxheadervalid_out;
o_rxpmaresetdone_out  #output wire [3 : 0] rxpmaresetdone_out;
o_rxprgdivresetdone_out   #output wire [3 : 0] rxprgdivresetdone_out;
o_rxstartofseq_out    #output wire [7 : 0] rxstartofseq_out;
o_txpmaresetdone_out  #output wire [3 : 0] txpmaresetdone_out;
o_txprgdivresetdone_out   #output wire [3 : 0] txprgdivresetdone_out;
"""   

class Open(Signal): pass

class Differential:
    def __init__(self, lanes):
        self.p = Signal(lanes)
        self.n = Signal.like(self.p)

class USPGTY4(Module):
    def __init__(self, platform, name, refclk):
        
        # high speed serial tx/rx
        LANES = 4
        self.gtyrx = Differential(LANES)
        self.gtytx = Differential(LANES)
        
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
        self.reset_clk_freerun = Signal()
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
            o_gtytxn_out = self.gtytx.n,
            o_gtytxp_out = self.gtytx.p,
            i_gtyrxn_in  = self.gtyrx.n,
            i_gtyrxp_in  = self.gtyrx.p,
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
                i_gtwiz_reset_clk_freerun_in = self.reset_clk_freerun,
                i_gtwiz_reset_all_in = self.reset_all,
            )
        )
        
        self.specials += Instance("gty4", **self.ip_ports)
