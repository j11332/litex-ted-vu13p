from migen.genlib.cdc import PulseSynchronizer, BusSynchronizer, MultiReg
from cores.xpm_fifo import XPMAsyncStreamFIFO
from litex.soc.interconnect.csr import *
from litex.soc.interconnect import stream

from cores.kyokko.layout import kyokkoStreamDesc
class KyokkoBlock(Module, AutoCSR):
    class _QSFPPortModel:
        def __init__(self, tx, rx):
            self.tx = tx
            self.rx = rx
        def connect(self, other):
            return [
                self.tx.connect(other.rx, keep={"ready"}),
                other.tx.connect(self.rx, keep={"ready"}),
                self.tx.ready.eq(1),
                other.tx.ready.eq(1),
            ]


    def __init__(self, platform, pads, refclk, cd="sys", cd_freerun="sys", lanes=4):
        self.sink_user_tx = stream.Endpoint(kyokkoStreamDesc(lanes=lanes))
        self.source_user_rx = stream.Endpoint(kyokkoStreamDesc(lanes=lanes))
    
        self.sink_qsfp_rx = stream.Endpoint(kyokkoStreamDesc(lanes=lanes))
        self.source_qsfp_tx = stream.Endpoint(kyokkoStreamDesc(lanes=lanes))

        # # #
 
        # Simulation
        xpm_enable = False
        self.comb += self.source_qsfp_tx.ready.eq(1)

        # Local clock domain for HSS Transceivers
        self.clock_domains.cd_datapath = cd_datapath =  ClockDomain()
        self.comb += [
            self.cd_datapath.clk.eq(ClockSignal("sim_gt")),
            self.cd_datapath.rst.eq(ResetSignal("sim_gt")),
        ]
        # CDC
        cdc_tx = ClockDomainsRenamer({"write" : cd, "read" : "datapath"})(
            stream.AsyncFIFO(kyokkoStreamDesc(lanes=lanes), 128, buffered=True))
        
        cdc_rx = ClockDomainsRenamer({"write" : "datapath", "read" : cd})(
            stream.AsyncFIFO(kyokkoStreamDesc(lanes=lanes), 128, buffered=True))

        self.comb += [
            self.sink_user_tx.connect(cdc_tx.sink),
            cdc_tx.source.connect(self.source_qsfp_tx),
            self.sink_qsfp_rx.connect(cdc_rx.sink),
            cdc_rx.source.connect(self.source_user_rx),
        ]
        
        self._reset = CSRStorage(fields=[
            CSRField("reset_pb", size=1, offset=0, description="""Write `1` to reset"""),
        ])
        
        self._status = CSRStatus(fields=[
            CSRField("lane_up", size=lanes),
            CSRField("channel_up", size=1),
        ])

        # Status register stub
        self.comb += [
            self._status.fields.channel_up.eq(1),
            self._status.fields.lane_up.eq(Replicate(1, lanes)),
        ]

    def getPortModel(self):
        return KyokkoBlock._QSFPPortModel(self.source_qsfp_tx, self.sink_qsfp_rx)
    
    @staticmethod
    def add_common_timing_constraints(platform):
        pass