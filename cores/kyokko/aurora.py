from litex.soc.interconnect.csr import AutoCSR, CSRField, CSRStatus, CSRStorage
from migen import *
from litex.soc.interconnect.stream import Endpoint
from migen.genlib.cdc import MultiReg
from cores.kyokko.layout import kyokkoStreamDesc
from cores.xpm_fifo import XPMAsyncStreamFIFO
from migen.genlib.resetsync import AsyncResetSynchronizer

class _ResetSequencer(Module):
    """ Aurora reset sequencer
                  _________
    do_reset    _/

    reset_pb    __/(pma_wait cyc.) 
                                   ________
    pma_init    __________________/

    """
    def __init__(self, pma_wait=50, reset_width=1):
        self.reset_pb = reset_pb = Signal()
        self.pma_init = pma_init = Signal()
        
        self.do_reset = do_reset = Signal()
        self.triggers = []
        
        pma_counter = Signal(bits_for(pma_wait))
        fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(do_reset,
                NextState("PMA_WAIT"),
                NextValue(pma_counter, 0)
            ),
            reset_pb.eq(0),
            pma_init.eq(0),
        )
        reset_counter = Signal(bits_for(reset_width))
        fsm.act("PMA_WAIT",
            If(pma_counter == pma_wait,
                NextState("RESET_WAIT"),
                NextValue(reset_counter, 0),
            ).Else(
                NextValue(pma_counter, pma_counter + 1)
            ),
            reset_pb.eq(1),
            pma_init.eq(0),
        )
        fsm.act("RESET_WAIT",
            If(reset_counter == reset_width,
                NextState("PMA_NEG_WAIT"),
                NextValue(pma_counter, 0),
            ).Else(
                NextValue(reset_counter, reset_counter + 1)
            ),
            reset_pb.eq(1),
            pma_init.eq(1),
        )
        fsm.act("PMA_NEG_WAIT",
            If(pma_counter == pma_wait,
                NextState("IDLE"),
            ).Else(
                NextValue(pma_counter, pma_counter + 1)
            ),
            reset_pb.eq(1),
            pma_init.eq(0),
        )
        self.submodules += fsm
    
    def add_reset(self, sig, edge = False):
        _do_reset = Signal()
        if edge is True:
            # Edge detection
            _sig_d = Signal()
            _sig_d2 = Signal()
            self.sync += [
                _sig_d.eq(sig),
                _sig_d2.eq(_sig_d),
                _do_reset.eq((sig)&(~_sig_d2))
            ]    
        self.triggers.append(_do_reset)

    def do_finalize(self):
        self.comb += self.do_reset.eq(reduce(or_, self.triggers))

class Aurora64b66b(Module, AutoCSR):
    def __init__(
        self, platform, 
        pads, refclk,
        cd_freerun = "clk100",
        freerun_clk_freq = int(100e6),
        with_ila = True):
        LANES=4        
        self.init_clk_locked = Signal()
        self.sink_user_tx = sink_user_tx = Endpoint(kyokkoStreamDesc(lanes=LANES))
        self.source_user_rx = source_user_rx = Endpoint(kyokkoStreamDesc(lanes=LANES))

        # Clock domain
        self.clock_domains.cd_dp = cd_dp = ClockDomain()
        
        # Reset sequencer
        self.reset_pb = Signal()
        self.pma_init = Signal()
        rg = ClockDomainsRenamer(cd_freerun)(
            _ResetSequencer(pma_wait=50, reset_width = freerun_clk_freq))
            
        import os.path
        srcdir = os.path.dirname(__file__)
        platform.add_sources(srcdir, "aurora_reset_seq.v")
        _vio_reset = Signal()
        _reset_seq_done = Signal()
        self.specials += Instance(
            "aurora_reset_seq", 
            i_init_clk = ClockSignal("clk100"),
            i_init_clk_locked = self.init_clk_locked,
            i_ext_reset_in = _vio_reset,
            i_are_sys_reset_in = cd_dp.rst,
            o_done = _reset_seq_done,
            o_are_reset_pb_out = self.reset_pb,
            o_are_pma_init_out = self.pma_init,
        )
        
        ip_vlnv = "xilinx.com:ip:aurora_64b66b"
        self.refname = "ar_" + pads.platform_info['quad']
        self.ip_cfg = {
            "CONFIG.CHANNEL_ENABLE"      : " ".join(pads.platform_info['channel']),
            "CONFIG.C_START_QUAD"        : pads.platform_info['quad'],
            "CONFIG.C_AURORA_LANES"      : "4",
            "CONFIG.C_LINE_RATE"         : "25.78125",
            "CONFIG.C_REFCLK_FREQUENCY"  : "161.1328125",
            "CONFIG.C_INIT_CLK"          : freerun_clk_freq // 1000000,
            "CONFIG.flow_mode"           : "None",
            "CONFIG.SINGLEEND_GTREFCLK"  : "false" if isinstance(refclk, Record) else "true",
            "CONFIG.C_GT_LOC_4"          : "4",
            "CONFIG.C_GT_LOC_3"          : "3",
            "CONFIG.C_GT_LOC_2"          : "2",
            "CONFIG.drp_mode"            : "Native",
            "CONFIG.SupportLevel"        : "1",
            "CONFIG.C_USE_BYTESWAP"      : "true",
            "CONFIG.C_GTWIZ_OUT"         : "false",
        }

        platform.add_tcl_ip(ip_vlnv, self.refname, self.ip_cfg)
        
        # clock buffer
        if isinstance(refclk, Record):
            self.ip_params = dict(
                i_gt_refclk1_n = refclk.n,
                i_gt_refclk1_p = refclk.p
            )
        else:
            self.ip_params = dict(
                i_refclk_in = refclk
            )

        self.ip_params.update(
            i_init_clk   = ClockSignal(cd_freerun),
            i_reset_pb   = self.reset_pb,
            i_power_down = 0b0,
            i_pma_init   = self.pma_init,
            i_loopback   = 0b0,
            i_rxp = pads.rx_p,
            i_rxn = pads.rx_n,
            o_txp = pads.tx_p,
            o_txn = pads.tx_n,
        )
        cdc_tx = XPMAsyncStreamFIFO(kyokkoStreamDesc(lanes=LANES),
            depth = 512,
            sync_stages = 4,
            xpm = True)
        cdc_tx = ClockDomainsRenamer({"read": cd_dp.name, "write" : "sys"})(cdc_tx)
        self.comb += self.sink_user_tx.connect(cdc_tx.sink)
        self.submodules.cdc_tx = cdc_tx

        cdc_rx = XPMAsyncStreamFIFO(kyokkoStreamDesc(lanes=LANES),
            depth = 512,
            sync_stages = 4,
            xpm = True)
        cdc_rx = ClockDomainsRenamer({"read": "sys", "write" : cd_dp.name})(cdc_rx)
        self.comb += cdc_rx.source.connect(self.source_user_rx)
        self.submodules.cdc_rx = cdc_rx
        
        if with_ila:
            import util.xilinx_ila
            for ep in [cdc_tx.source, cdc_rx.sink]:
                for s in [ep.valid, ep.ready, ep.last]:
                    platform.ila.add_probe(s, cd_dp.clk, trigger=True)
                for s in ep.payload.flatten():
                    platform.ila.add_probe(s, cd_dp.clk, trigger=False)

        self._status = CSRStatus(fields=[
            CSRField("reset_pb", size=1),
            CSRField("pma_init", size=1),
            CSRField("mmcm_not_locked", size=1),
        ])

        # Status Register
        mmcm_not_locked = Signal()
        self.specials += MultiReg(self.reset_pb, self._status.fields.reset_pb, odomain="sys", n=2)
        self.specials += MultiReg(self.pma_init, self._status.fields.pma_init, odomain="sys", n=2)
        self.specials += MultiReg(mmcm_not_locked, self._status.fields.mmcm_not_locked, odomain="sys", n=2)

        self.ip_params.update(
            i_s_axi_tx_tdata    = cdc_tx.source.data,
            i_s_axi_tx_tkeep    = Replicate(0b1, len(cdc_tx.source.data)//8),
            i_s_axi_tx_tlast    = cdc_tx.source.last,
            i_s_axi_tx_tvalid   = cdc_tx.source.valid,
            o_s_axi_tx_tready   = cdc_tx.source.ready,
            o_m_axi_rx_tdata    = self.cdc_rx.sink.data,
            o_m_axi_rx_tkeep    = Signal(),
            o_m_axi_rx_tlast    = self.cdc_rx.sink.last,
            o_m_axi_rx_tvalid   = self.cdc_rx.sink.valid,
        )

        lane_up                     = Signal(LANES)
        channel_up                  = Signal()
        hard_err                    = Signal()
        soft_err                    = Signal()
        # Status Output
        _gt_qpllrefclklost_quad1_out = Signal()
        _gt_qplllock_quad1_out = Signal()
        self.ip_params.update(
            o_gt_qpllclk_quad1_out        = Signal(),
            o_gt_qpllrefclk_quad1_out     = Signal(),
            o_gt_qpllrefclklost_quad1_out = _gt_qpllrefclklost_quad1_out,
            o_gt_qplllock_quad1_out       = _gt_qplllock_quad1_out,
            o_gt_reset_out                = Signal(),
            o_gt_powergood                = Signal(),
            o_mmcm_not_locked_out         = mmcm_not_locked,
            o_sys_reset_out               = cd_dp.rst,
            o_user_clk_out                = cd_dp.clk,
            o_link_reset_out              = Signal(),
            o_sync_clk_out                = Signal(),
            o_lane_up                     = lane_up,
            o_channel_up                  = channel_up,
            o_hard_err                    = hard_err,
            o_soft_err                    = soft_err,
        )
        from util.xilinx_vio import XilinxVIO
        self.submodules.vio = vio = XilinxVIO(platform)
        vio.add_input_probe(lane_up)
        vio.add_input_probe(channel_up)
        vio.add_input_probe(hard_err)
        vio.add_input_probe(soft_err)
        vio.add_input_probe(self.pma_init)
        vio.add_input_probe(self.reset_pb)
        vio.add_input_probe(_reset_seq_done)
        vio.add_input_probe(_gt_qpllrefclklost_quad1_out)
        vio.add_input_probe(_gt_qplllock_quad1_out)
        vio.add_output_probe(_vio_reset)

        for _n in range(0, LANES):
            self.ip_params.update({
                f"i_gt{_n}_drpaddr"  : 0,
                f"i_gt{_n}_drpdi"    : Replicate(0b0, 10),
                f"o_gt{_n}_drpdo"    : Signal(16),
                f"i_gt{_n}_drpen"    : 0,
                f"o_gt{_n}_drprdy"   : Signal(),
                f"i_gt{_n}_drpwe"    : 0,
            })
        
        self.specials += Instance(
            self.refname,
            name=self.refname + "_i",
            **self.ip_params)


