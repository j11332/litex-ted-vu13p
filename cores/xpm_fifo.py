from migen import *
from litex.soc.interconnect import stream

class XPMStreamFIFO(Module):
    def __init__(self, layout, depth, buffered=False, xpm=True):
        if xpm == False:
            self.sink = stream.Endpoint(layout)
            self.source = stream.Endpoint(layout)
            self.submodules.fifo = fifo = stream.SyncFIFO(layout, depth=depth, buffered=buffered)
            self.comb += [
                self.sink.connect(fifo.sink),
                fifo.source.connect(self.source)
            ]
        else:
            self.sink = stream.Endpoint(layout)
            self.source = stream.Endpoint(layout)

            desc = self.sink.description
            data_layout = [
                ("payload", desc.payload_layout),
                ("param",   desc.param_layout),
                ("first",   1),
                ("last",    1)
            ]

            self._fifo_in  = fifo_in  = Record(data_layout)
            self._fifo_out = fifo_out = Record(data_layout)

            self.comb += [
                fifo_in.payload.eq(self.sink.payload),
                fifo_in.param.eq(self.sink.param),

                self.source.payload.eq(fifo_out.payload),
                self.source.param.eq(fifo_out.param),
            ]
            _tdata_len = ((len(fifo_in.raw_bits()) + 7) // 8) * 8
            _padding_len = _tdata_len - len(fifo_in.raw_bits())

            self.xpm_params = dict(
                p_CASCADE_HEIGHT      = 0,
                p_CDC_SYNC_STAGES     = 2,
                p_CLOCKING_MODE       = "common_clock",
                p_ECC_MODE            = "no_ecc",
                p_FIFO_DEPTH          = depth,
                p_FIFO_MEMORY_TYPE    = "auto",
                p_PROG_EMPTY_THRESH   = 10,
                p_SIM_ASSERT_CHK      = 0,
                p_TDATA_WIDTH         = _tdata_len,
                p_TDEST_WIDTH         = 1,
                p_TID_WIDTH           = 1,
                p_TUSER_WIDTH         = 1,
                p_USE_ADV_FEATURES    = "1000",
                o_almost_empty_axis   = Signal(),
                o_almost_full_axis    = Signal(),
                o_dbiterr_axis        = Signal(),
                i_m_aclk              = ClockSignal(),
                o_m_axis_tdata        = Cat(fifo_out.raw_bits(), Signal(_padding_len)),
                o_m_axis_tdest        = Signal(),
                o_m_axis_tid          = Signal(),
                o_m_axis_tkeep        = Signal(),
                o_m_axis_tlast        = self.source.last,
                o_m_axis_tstrb        = Signal(),
                o_m_axis_tuser        = self.source.first,
                o_m_axis_tvalid       = self.source.valid,
                i_m_axis_tready       = self.source.ready,
                o_prog_empty_axis     = Signal(),
                o_prog_full_axis      = Signal(),
                o_rd_data_count_axis  = Signal(),
                o_sbiterr_axis        = Signal(),
                o_wr_data_count_axis  = Signal(),
                i_injectdbiterr_axis  = 0b0,
                i_injectsbiterr_axis  = 0b0,
                i_s_aclk              = ClockSignal(),
                i_s_aresetn           = ~ResetSignal(),
                i_s_axis_tdata        = Cat(fifo_in.raw_bits(), Replicate(C(0b0), _padding_len)),
                i_s_axis_tdest        = 0b0,
                i_s_axis_tid          = 0b0,
                i_s_axis_tkeep        = 0b0,
                i_s_axis_tlast        = self.sink.last,
                i_s_axis_tstrb        = 0b0,
                i_s_axis_tuser        = self.sink.first,
                i_s_axis_tvalid       = self.sink.valid,
                o_s_axis_tready       = self.sink.ready,
            )
    
    def do_finalize(self):
        if hasattr(self, "xpm_params"):
            self.specials += Instance("xpm_fifo_axis", name = "xpm_fifo_i",
                **self.xpm_params)

class XPMAsyncStreamFIFO(Module):
    def __init__(self, layout, 
        depth=16, sync_stages=2, buffered=False, xpm=True):

        cd_sink="write"
        cd_source="read"

        if xpm == False:
            self.sink = stream.Endpoint(layout)
            self.source = stream.Endpoint(layout)
            self.submodules.fifo = fifo = stream.AsyncFIFO(layout, depth=depth, buffered=buffered)
            self.comb += [
                self.sink.connect(fifo.sink),
                fifo.source.connect(self.source)
            ]
        else:
            self.sink = stream.Endpoint(layout)
            self.source = stream.Endpoint(layout)

            desc = self.sink.description
            data_layout = [
                ("payload", desc.payload_layout),
                ("param",   desc.param_layout),
            ]

            self._fifo_in  = fifo_in  = Record(data_layout)
            self._fifo_out = fifo_out = Record(data_layout)

            self.comb += [
                fifo_in.payload.eq(self.sink.payload),
                fifo_in.param.eq(self.sink.param),

                self.source.payload.eq(fifo_out.payload),
                self.source.param.eq(fifo_out.param),
            ]
            _tdata_len = ((len(fifo_in.raw_bits()) + 7) // 8) * 8
            _padding_len = _tdata_len - len(fifo_in.raw_bits())

            self.xpm_params = dict(
                p_CASCADE_HEIGHT      = 0,  # 0 = auto
                p_CDC_SYNC_STAGES     = sync_stages,
                p_CLOCKING_MODE       = "independent_clock",
                p_ECC_MODE            = "no_ecc",
                p_FIFO_DEPTH          = depth,
                p_FIFO_MEMORY_TYPE    = "auto",
                p_PROG_EMPTY_THRESH   = 10,
                p_SIM_ASSERT_CHK      = 0,
                p_TDATA_WIDTH         = _tdata_len,
                p_TDEST_WIDTH         = 1,
                p_TID_WIDTH           = 1,
                p_TUSER_WIDTH         = 1,
                p_USE_ADV_FEATURES    = "1000",
                o_almost_empty_axis   = Signal(),
                o_almost_full_axis    = Signal(),
                o_dbiterr_axis        = Signal(),
                i_m_aclk              = ClockSignal(cd_source),
                o_m_axis_tdata        = Cat(fifo_out.raw_bits(), Signal(_padding_len)) if _padding_len != 0 else fifo_out.raw_bits(),
                o_m_axis_tdest        = Signal(),
                o_m_axis_tid          = Signal(),
                o_m_axis_tkeep        = Signal(),
                o_m_axis_tlast        = self.source.last,
                o_m_axis_tstrb        = Signal(),
                o_m_axis_tuser        = self.source.first,
                o_m_axis_tvalid       = self.source.valid,
                i_m_axis_tready       = self.source.ready,
                o_prog_empty_axis     = Signal(),
                o_prog_full_axis      = Signal(),
                o_rd_data_count_axis  = Signal(),
                o_sbiterr_axis        = Signal(),
                o_wr_data_count_axis  = Signal(),
                i_injectdbiterr_axis  = 0b0,
                i_injectsbiterr_axis  = 0b0,
                i_s_aclk              = ClockSignal(cd_sink),
                i_s_aresetn           = ~ResetSignal(cd_sink),
                i_s_axis_tdata        = Cat(fifo_in.raw_bits(), Replicate(C(0b0), _padding_len)),
                i_s_axis_tdest        = 0b0,
                i_s_axis_tid          = 0b0,
                i_s_axis_tkeep        = 0b0,
                i_s_axis_tlast        = self.sink.last,
                i_s_axis_tstrb        = 0b0,
                i_s_axis_tuser        = self.sink.first,
                i_s_axis_tvalid       = self.sink.valid,
                o_s_axis_tready       = self.sink.ready,
            )
    
    def do_finalize(self):
        if hasattr(self, "xpm_params"):
            self.specials += Instance("xpm_fifo_axis", name="xpm_afifo_0",
                **self.xpm_params)
