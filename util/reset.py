from migen import *
from functools import reduce
from operator import and_

class _ShiftSync(Module):
    def __init__(self, sr_len):

        self.async_i = Signal(reset_less = True)
        self.sync_o  = Signal(reset_less = True)
        
        sr = Signal(sr_len, reset_less = True)
        self.sync += [
            sr.eq(Cat(self.async_i, sr[:sr_len-1])),
            self.sync_o.eq(reduce(and_, sr)),
        ]
class PoRCounter(Module):
    def __init__(self, width = 10):
        self.reset_com = Signal(reset=1)
        self.timeout = Signal()

        # # #
        counter = Signal(width)
        self.comb += self.timeout.eq(reduce(and_, counter))
        self.sync += [
            If(self.timeout == 1,
                counter.eq(counter),
            ).Else(
                counter.eq(counter + 1),
            ),
            If(self.timeout,
                self.reset_com.eq(0),
            ).Else(
                self.reset_com.eq(1),
            )
        ]

class XilinxStartupReset(Module):
    def __init__(self):
        
        self.clock_domains.cd_cfgmclk = cd_cfgmclk = ClockDomain()
        self.clock_domains.cd_cfgmclk_por = cd_cfgmclk_por = ClockDomain()
        self.clock_domains.cd_cfgmclk_mmcm = cd_cfgmclk_mmcm = ClockDomain()

        # # #
        
        eos = Signal(reset_less=True)
        _cfgmclk_unbuffered = Signal(reset_less=True)
        
        self.specials += Instance(
            "STARTUPE3", name="startupe3_inst",
            o_CFGCLK        = Signal(),
            o_CFGMCLK       = _cfgmclk_unbuffered,
            o_DI            = Signal(4),
            i_DO            = Replicate(0b0, 4),
            i_DTS           = Replicate(0b1, 4),
            o_EOS           = eos,
            i_FCSBO         = 0b0,
            i_FCSBTS        = 0b1,
            i_GSR           = 0b0,
            i_GTS           = 0b0,
            i_KEYCLEARB     = 0b1,
            i_PACK          = 0b0,
            o_PREQ          = Signal(),
            i_USRCCLKO      = 0b0,
            i_USRCCLKTS     = 0b1,
            i_USRDONEO      = 0b0,
            i_USRDONETS     = 0b1,
        )

        self.specials += Instance(
            "BUFG",
            i_I = _cfgmclk_unbuffered,
            o_O = cd_cfgmclk.clk,
        )

        self.clock_domains.cd_reset_int = cd_cfgmclk_int = ClockDomain(reset_less=True)
        self.comb += cd_cfgmclk_int.clk.eq(cd_cfgmclk.clk),
        eos_sync = ClockDomainsRenamer(cd_cfgmclk_int.name)(_ShiftSync(10))
        self.submodules += eos_sync
        
        self.comb += [ 
            eos_sync.async_i.eq(eos),
            cd_cfgmclk.rst.eq(~eos_sync.sync_o),
        ]
        
        por_counter = ClockDomainsRenamer(cd_cfgmclk.name)(PoRCounter(10))
        self.comb += [
            cd_cfgmclk_por.clk.eq(cd_cfgmclk.clk),
            cd_cfgmclk_por.rst.eq(por_counter.reset_com)
        ]
        self.submodules += por_counter

        mmcm_counter = ClockDomainsRenamer(cd_cfgmclk_por.name)(PoRCounter(10))
        self.comb += [
            cd_cfgmclk_mmcm.clk.eq(cd_cfgmclk.clk),
            cd_cfgmclk_mmcm.rst.eq(mmcm_counter.reset_com)
        ]
        self.submodules += mmcm_counter
 

if __name__ == "__main__":
    import util.reset
    from migen.fhdl.verilog import convert
    xsr = util.reset.XilinxStartupReset()
    convert(xsr, ios=set([
        xsr.cd_cfgmclk.clk, xsr.cd_cfgmclk.rst,
        xsr.cd_cfgmclk_por.clk, xsr.cd_cfgmclk_por.rst,
        xsr.cd_cfgmclk_mmcm.clk, xsr.cd_cfgmclk_mmcm.rst])).write("test.v")