from migen import *
from migen.genlib.cdc import MultiReg, BusSynchronizer, PulseSynchronizer

_vio_vlnv = "xilinx.com:ip:vio"

class XilinxVIO(Module):
    """ Xilinx VIO wrapper
    Probe can be added with `add_input_probe()` or `add_output_probe()`

    Parameters
    ----------
    platform: XilinxPlatform
        `Platform` object
    """
    
    # Instance counter
    instances = 0

    def __init__(self, platform):
        self.platform = platform
        self.ip_params = dict()
        self.probe_in = []
        self.probe_out = []
        self.refname = f"vio_{self.instances}"
        XilinxVIO.instances += 1
        
    def add_input_probe(self, sig, cd=None):
        """ Add probe for input signal `sig`
        Parameters
        ----------
        sig : Signal
            `Signal` to probe
        cd  : `ClockDomain` or `str`
            ClockDomain of `sig`
        """
        _probe = Signal(len(sig), name=sig.backtrace[-1][0], reset_less=True)
        _probe.attr.add(("dont_touch", "true"))
        if cd is not None:
            _src_clk = cd.clk if isinstance(cd, ClockDomain) else ClockSignal(cd)
        
        # FIXME: Better CDC with migen
        self.specials += Instance(
            "xpm_cdc_array_single",
            p_DEST_SYNC_FF  = 4,
            p_SRC_INPUT_REG = 0 if cd is None else 1,
            p_WIDTH         = len(sig),
            i_src_in        = sig,
            i_src_clk       = 0b0 if cd is None else _src_clk,
            i_dest_clk      = ClockSignal(),
            o_dest_out      = _probe,
            name            = "cdc_" + sig.backtrace[-1][0]
        )
        self.probe_in += [_probe]
        
    
    def add_output_probe(self, sig):
        """ Add output probe for signal `sig`
        Parameters
        ----------
        sig : Signal
            `Signal` to probe
        """
        self.probe_out += [sig]

    def do_finalize(self):
        _ip_config = {
            "CONFIG.C_NUM_PROBE_IN" : len(self.probe_in),
            "CONFIG.C_NUM_PROBE_OUT" : len(self.probe_out),
        }
        _ip_params = {
            "i_clk" : ClockSignal()
        }

        for i, sig in enumerate(self.probe_in):
            _ip_config.update({ f"CONFIG.C_PROBE_IN{i}_WIDTH": len(sig) })
            _ip_params.update({ f"i_probe_in{i}" : sig })
        
        for i, sig in enumerate(self.probe_out):
            _ip_config.update({ f"CONFIG.C_PROBE_OUT{i}_WIDTH": len(sig) })
            _ip_params.update({ f"o_probe_out{i}" : sig })
        
        self.platform.add_tcl_ip(_vio_vlnv, self.refname, _ip_config)

        self.specials += Instance(
            self.refname,
            name=self.refname + "_i",
            **_ip_params)
