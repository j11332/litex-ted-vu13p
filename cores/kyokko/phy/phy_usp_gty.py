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

class USPGTY(Module):
    def __init__(self, platform, name, pads, phy_pads):
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
        gtrefclk = pads['gtrefclk']
        if isinstance(gtrefclk, Record):
            self.gtrefclk = Signal()
            self.specials.refclk_buf = Instance("IBUFDS_GTE4", "refclk_buf",
                    i_I = gtrefclk.p, i_IB = gtrefclk.n,
                    i_CEB = 0b0, o_O = self.gtrefclk)
        else:
            self.gtrefclk = gtrefclk
        
        self.hs = pads['hs']  
        self.lane_count = 4
        self.txuserclk = phy_pads.TXCLK
        self.rxuserclk = phy_pads.RXCLK
        self.rxpath_reset = phy_pads.RXPATH_RST
        self.tx_ready = ~phy_pads.TXRST
        self.rx_ready = ~phy_pads.RXRST
        self.tx_userdata = phy_pads.TXS
        self.rx_userdata = phy_pads.RXS
        self.tx_header = phy_pads.TXHDR
        self.rx_header = phy_pads.RXHDR
        self.rx_slip = phy_pads.RXSLIP
                        
        self.ip_ports = dict(
            i_gtwiz_userclk_tx_reset_in = 0b0,
            o_gtwiz_userclk_tx_srcclk_out = Open(),
            o_gtwiz_userclk_tx_usrclk_out = Open(),
            o_gtwiz_userclk_tx_usrclk2_out = self.txuserclk,
            o_gtwiz_userclk_tx_active_out = Open(),
            i_gtwiz_userclk_rx_reset_in = 0b0,
            o_gtwiz_userclk_rx_srcclk_out = Open(),
            o_gtwiz_userclk_rx_usrclk_out = Open(),
            o_gtwiz_userclk_rx_usrclk2_out = self.rxuserclk,
            o_gtwiz_userclk_rx_active_out = Open(),
            i_gtwiz_reset_clk_freerun_in = ClockSignal("clk100"),
            i_gtwiz_reset_all_in = ResetSignal("clk100"),
            i_gtwiz_reset_tx_pll_and_datapath_in = 0b0,
            i_gtwiz_reset_tx_datapath_in = 0b0,
            i_gtwiz_reset_rx_pll_and_datapath_in = 0b0,
            i_gtwiz_reset_rx_datapath_in = self.rxpath_reset,
            o_gtwiz_reset_rx_cdr_stable_out = Open(),
            o_gtwiz_reset_tx_done_out = self.tx_ready,
            o_gtwiz_reset_rx_done_out = self.rx_ready,
            i_gtwiz_userdata_tx_in = self.tx_userdata,
            o_gtwiz_userdata_rx_out = self.rx_userdata,
            i_gtrefclk00_in = self.gtrefclk,
            o_qpll0outclk_out = Open(),
            o_qpll0outrefclk_out = Open(),
            i_gtyrxn_in = self.hs.rxn,
            i_gtyrxp_in = self.hs.rxp,
            i_rxgearboxslip_in = self.rx_slip,
            i_txheader_in = self.tx_header,
            i_txsequence_in = None,
            o_gtpowergood_out = Open(),
            o_gtytxn_out = self.hs.txn,
            o_gtytxp_out = self.hs.txp,
            o_rxdatavalid_out = Open(),
            o_rxheader_out = self.rx_header,
            o_rxheadervalid_out = Open(),
            o_rxpmaresetdone_out = Open(),
            o_rxprgdivresetdone_out = Open(),
            o_rxstartofseq_out = Open(),
            o_txpmaresetdone_out = Open(),
            o_txprgdivresetdone_out = Open(),
        )
        
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
        
        self.platform.toolchain.pre_synthesis_commands += [
            f"generate_target all [get_ips {self.name}]",
        ]
        
        self.specials.phy = Instance(self.name, **self.ip_ports)