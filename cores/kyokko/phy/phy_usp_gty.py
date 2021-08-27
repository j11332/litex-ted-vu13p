#!/usr/bin/env python3
import os
import json
from migen import *
from litex.soc.interconnect import stream

class Open(Signal): pass

class USPGTY4(Module):
    def __init__(self, pads, refclk_connection, platform, name):
        lanes = 4
        # RX Interface
        self.rx_data = Signal(lanes * 64)
        self.rx_header = Signal(lanes * 6)
        self.rx_gearbox_slip = Signal(lanes)
        self.rx_reset_done = Signal()
        self.rx_userclk = Signal()
        self.rx_userclk_reset = Signal()
        self.rx_reset_dp = Signal()
        self.rx_reset_dp_and_pll = Signal()
        # TX Interface
        self.tx_data = Signal(lanes * 64)
        self.tx_header = Signal(lanes * 6)
        self.tx_sequence = Signal(lanes * 7)
        self.tx_reset_done = Signal()
        self.tx_userclk = Signal()
        self.tx_userclk_reset = Signal()
        self.tx_reset_dp = Signal()
        self.tx_reset_dp_and_pll = Signal()
        
        # Common
        self.reset_all = Signal()
        
        # # #
        self.name = name
        self.platform = platform
        self.ip_params = {
            "CONFIG.CHANNEL_ENABLE"          : "X0Y23 X0Y22 X0Y21 X0Y20",
            "CONFIG.FREERUN_FREQUENCY"       : "100",
            "CONFIG.LOCATE_RX_USER_CLOCKING" : "CORE",
            "CONFIG.LOCATE_TX_USER_CLOCKING" : "CORE",
            "CONFIG.PRESET"                  : "GTY-Aurora_64B66B",
            "CONFIG.RX_CB_MAX_LEVEL"         : "2",
            "CONFIG.RX_DATA_DECODING"        : "64B66B_ASYNC",
            "CONFIG.RX_JTOL_FC"              : "10",
            "CONFIG.RX_LINE_RATE"            : "25.78125",
            "CONFIG.RX_MASTER_CHANNEL"       : "X0Y23",
            "CONFIG.RX_OUTCLK_SOURCE"        : "RXPROGDIVCLK",
            "CONFIG.RX_REFCLK_FREQUENCY"     : "161.1328125",
            "CONFIG.RX_REFCLK_SOURCE"        : "",
            "CONFIG.TXPROGDIV_FREQ_VAL"      : "390.625",
            "CONFIG.TX_DATA_ENCODING"        : "64B66B_ASYNC",
            "CONFIG.TX_LINE_RATE"            : "25.78125",
            "CONFIG.TX_MASTER_CHANNEL"       : "X0Y23",
            "CONFIG.TX_OUTCLK_SOURCE"        : "TXPROGDIVCLK",
            "CONFIG.TX_REFCLK_FREQUENCY"     : "161.1328125",
        }
        gtrefclk = pads['gtrefclk']
        if isinstance(gtrefclk, Record):
            self.gtrefclk = Signal()
            self.specials.refclk_buf = Instance(
                "IBUFDS_GTE4",
                name="refclk_buf",
                i_I = gtrefclk.p,
                i_IB = gtrefclk.n,
                i_CEB = 0b0,
                o_O = self.gtrefclk
            )
        else:
            self.gtrefclk = gtrefclk

        self.ip_ports = dict(
            i_gtwiz_userdata_tx_in               = self.tx_userdata,
            i_txheader_in                        = self.tx_header,
            i_txsequence_in                      = self.tx_sequence,
            o_gtwiz_reset_tx_done_out            = self.tx_reset_done,
            o_gtwiz_userclk_tx_usrclk2_out       = self.tx_userclk,
            i_gtwiz_userclk_tx_reset_in          = self.tx_userclk_reset,
            i_gtwiz_reset_tx_pll_and_datapath_in = self.tx_reset_dp,
            i_gtwiz_reset_tx_datapath_in         = self.tx_reset_dp_and_pll,
        )
        
        self.ip_ports.update(dict(
            o_gtwiz_userdata_rx_out               = self.rx_data,
            o_rxheader_out                        = self.rx_header,
            i_rxgearboxslip_in                    = self.rx_gearbox_slip,
            o_gtwiz_reset_rx_done_out             = self.rx_reset_done,
            o_gtwiz_userclk_rx_usrclk2_out        = self.rx_userclk,
            i_gtwiz_userclk_rx_reset_in           = self.rx_userclk_reset,
            i_gtwiz_reset_rx_datapath_in          = self.rx_reset_dp,
            i_gtwiz_reset_rx_pll_and_datapath_in  = self.rx_reset_dp_and_pll,
        ))

        self.ip_ports.update(dict(
            i_gtyrxn_in  = pads.rxn,
            i_gtyrxp_in  = pads.rxp,
            o_gtytxn_out = pads.txn,
            o_gtytxp_out = pads.txp,
        ))
        
        # i_gtrefclk00_in = self.gtrefclk
        self.ip_ports.update(dict(
            i_gtwiz_reset_clk_freerun_in = ClockSignal(cd=self.cd),
            i_gtwiz_reset_all_in = ResetSignal(cd=self.cd)
        ))

        self.ip_ports.update(refclk_connection)
        self.ip_ports.update(dict(
            o_gtwiz_userclk_tx_srcclk_out = Open(),
            o_gtwiz_userclk_tx_usrclk_out = Open(),
            o_gtwiz_userclk_tx_active_out = Open(),
            o_gtwiz_userclk_rx_srcclk_out = Open(),
            o_gtwiz_userclk_rx_usrclk_out = Open(),
            o_gtwiz_userclk_rx_active_out = Open(),
            o_gtwiz_reset_rx_cdr_stable_out = Open(),
            o_qpll0outclk_out = Open(),
            o_qpll0outrefclk_out = Open(),
            o_gtpowergood_out = Open(),
            o_rxdatavalid_out = Open(),
            o_rxheadervalid_out = Open(),
            o_rxpmaresetdone_out = Open(),
            o_rxprgdivresetdone_out = Open(),
            o_rxstartofseq_out = Open(),
            o_txpmaresetdone_out = Open(),
            o_txprgdivresetdone_out = Open(),
        ))

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