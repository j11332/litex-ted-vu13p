#!/usr/bin/env python3
from migen import *
from litex.soc.interconnect import stream
from cores.kyokko.phy.phy_usp_gty import USPGTY4
import os.path
from litex.build.xilinx import XilinxPlatform

from cores.xpm_fifo import XPMAsyncStreamFIFO

# create_ip -vlnv xilinx.com:ip:fifo_generator:* -module_name 
_xilinx_fifo_66x512_async_ip = {
    "CONFIG.Data_Count_Width"           : "9",
    "CONFIG.Enable_Safety_Circuit"      : "true",
    "CONFIG.Fifo_Implementation"        : "Independent_Clocks_Block_RAM",
    "CONFIG.Full_Flags_Reset_Value"     : "1",
    "CONFIG.Full_Threshold_Assert_Value": "509",
    "CONFIG.Full_Threshold_Negate_Value": "508",
    "CONFIG.Input_Data_Width"           : "66",
    "CONFIG.Input_Depth"                : "512",
    "CONFIG.Output_Data_Width"          : "66",
    "CONFIG.Output_Depth"               : "512",
    "CONFIG.Read_Data_Count_Width"      : "9",
    "CONFIG.Reset_Type"                 : "Asynchronous_Reset",
    "CONFIG.Valid_Flag"                 : "true",
    "CONFIG.Write_Data_Count_Width"     : "9",
}

class Kyokko(Module):
    def __init__(self, platform, phy, bond_ch = 4, cd_freerun="clk100"):
        self.user_tx_sink = stream.Endpoint([("data", 64 * bond_ch)])
        self.user_rx_source = stream.Endpoint([("data", 64 * bond_ch)])
        self.init_clk_locked = Signal()
        
        # # #
        if isinstance(platform, XilinxPlatform):
            platform.add_tcl_ip("xilinx.com:ip:fifo_generator", "fifo_66x512_async", _xilinx_fifo_66x512_async_ip)
        else: 
            raise NotImplementedError()

        # TX User I/F
        self.kyokko_params = dict(
            i_s_axis_tx_tvalid = self.user_tx_sink.valid,
            i_s_axis_tx_tlast = self.user_tx_sink.last,
            i_s_axis_tx_tdata = self.user_tx_sink.data,
            o_s_axis_tx_tready = self.user_tx_sink.ready
        )

        # RX User I/F
        self.kyokko_params.update(
            o_m_axis_rx_tvalid = self.user_rx_source.valid,
            o_m_axis_rx_tlast = self.user_rx_source.last,
            o_m_axis_rx_tdata = self.user_rx_source.data
        )
        self.comb += self.user_rx_source.ready.eq(1)
        self.submodules.phy = phy
        self.kyokko_params.update(
            i_clk = ClockSignal(cd_freerun),
            i_reset = ResetSignal(cd_freerun),
            o_gtwiz_userclk_tx_reset_out = phy.userclk_tx_reset,
            i_gtwiz_userclk_tx_usrclk2_in = phy.userclk_tx_usrclk2,
            o_gtwiz_userclk_rx_reset_out = phy.userclk_rx_reset,
            i_gtwiz_userclk_rx_usrclk2_in = phy.userclk_rx_usrclk2,
            o_gtwiz_reset_all_out = phy.reset_all,
            o_gtwiz_reset_tx_pll_and_datapath_out = phy.reset_tx_pll_and_datapath,
            o_gtwiz_reset_tx_datapath_out = phy.reset_tx_datapath,
            o_gtwiz_reset_rx_pll_and_datapath_out = phy.reset_rx_pll_and_datapath,
            o_gtwiz_reset_rx_datapath_out = phy.reset_rx_datapath,
            i_gtwiz_reset_tx_done_in = phy.reset_tx_done,
            i_gtwiz_reset_rx_done_in = phy.reset_rx_done,
            o_gtwiz_userdata_tx_out = phy.userdata_tx,
            i_gtwiz_userdata_rx_in = phy.userdata_rx,
            o_rxgearboxslip_out = phy.rxgearboxslip,
            o_txheader_out = phy.txheader,
            i_rxheader_in = phy.rxheader,
            o_txsequence_out = phy.txsequence,
        )
    @staticmethod
    def add_sources(platform):
        srcdir = os.path.join(os.path.dirname(__file__), "rtl")
        srcdir = os.path.join(srcdir, "verilog")
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
            "teng-sc.v",
            "kyokko_cb_wrapper.v",
            project=True)
            
    def do_finalize(self):
        self.specials += Instance("kyokko_cb_wrapper", **self.kyokko_params)

from litex.soc.interconnect.csr import *
from migen.genlib.cdc import PulseSynchronizer, BusSynchronizer, MultiReg
class KyokkoBlock(Module, AutoCSR):
    def __init__(self, platform, pads, refclk, cd="sys", cd_freerun="sys", lanes=4):
        _dp_layout = stream.EndpointDescription([
                ("data", 64 * lanes),
                # ("keep", (64 * lanes) // 8)
            ]
        )
        self.platform = platform
        self.sink_user_tx = stream.Endpoint(_dp_layout)
        self.source_user_rx = stream.Endpoint(_dp_layout)
        self.clock_domains.cd_datapath = ClockDomain()
        
        # CDC
        self.submodules.cdc_tx = cdc_tx = ClockDomainsRenamer({"write" : cd, "read" : "datapath"})(
            XPMAsyncStreamFIFO(self.sink_user_tx.description, depth=128, buffered=True, sync_stages=4))
        
        self.submodules.cdc_rx = cdc_rx = ClockDomainsRenamer({"write" : "datapath", "read" : cd})(
            XPMAsyncStreamFIFO(self.source_user_rx.description, depth=128, buffered=True, sync_stages=4))

        self.comb += [
            self.sink_user_tx.connect(cdc_tx.sink),
            cdc_rx.source.connect(self.source_user_rx)
        ]
        
        self._reset = CSRStorage(fields=[
            CSRField("reset_pb", size=1, offset=0, description="""Write `1` to reset"""),
        ])
        self._status = CSRStatus(fields=[
            CSRField("lane_up", size=lanes),
            CSRField("channel_up", size=1),
        ])

        # Status Register
        channel_up = Signal()
        self.specials += MultiReg(channel_up, self._status.fields.channel_up, odomain=cd, n=2)
        
        lane_up = Signal(lanes)
        self.specials += MultiReg(lane_up, self._status.fields.lane_up, odomain=cd, n=2)
                
        self.core_params = dict(
            i_clk         = ClockSignal(cd_freerun),
            i_reset       = self._reset.fields.reset_pb,
            o_channel_up  = channel_up,
            o_lane_up     = lane_up,
            o_user_clk    = ClockSignal(cd="datapath"),
            
            # User data TX/RX
            i_s_axis_tx_tdata   = cdc_tx.source.data,
            i_s_axis_tx_tlast   = cdc_tx.source.last,
            i_s_axis_tx_tvalid  = cdc_tx.source.valid,
            o_s_axis_tx_tready  = cdc_tx.source.ready,
            o_m_axis_rx_tdata   = cdc_rx.sink.data,
            o_m_axis_rx_tlast   = cdc_rx.sink.last,
            o_m_axis_rx_tvalid  = cdc_rx.sink.valid,

            # GTY Pads
            i_gtyrxn            = pads.rx_n,
            i_gtyrxp            = pads.rx_p,
            o_gtytxn            = pads.tx_n,
            o_gtytxp            = pads.tx_p,
            i_gt_refclk_clk_p   = refclk.clk_p if hasattr(refclk, "clk_p") else refclk.p,
            i_gt_refclk_clk_n   = refclk.clk_n if hasattr(refclk, "clk_n") else refclk.n,
        )

    def do_finalize(self):
        self.platform.add_platform_command("""
set_false_path -from [get_pins -match_style ucf */tx/init/RX_STAT_TX_reg[*]/C]
set_false_path -from [get_pins -match_style ucf */rxinit/LINK_ERR_TIMER_reg[*]/C]
set_false_path -from [get_pins -match_style ucf */rxinit/RXSLIP_LIMIT_reg/C] -to [get_pins -match_style ucf */rxrst/RXSLIP_LIMITi_reg/D]
set_false_path -to [get_pins -match_style ucf */RXRST100i_reg/*]""")
        self.specials += Instance("kyokko_gty4", **self.core_params, name="kyokko_gty4_i")
    
    def add_timing_constraints(self, platform, padgroup_name):
        pass
    