from migen import *
_vio_vlnv = "xilinx.com:ip:vio"

class XilinxVIO(Module):
    instances = 0
    def __init__(self, platform):
        self.platform = platform
        self.ip_params = dict()
        self.probe_in = []
        self.probe_out = []
        self.refname = f"vio_{self.instances}"
        XilinxVIO.instances += 1
        
    def add_input_probe(self, sig):
        self.probe_in += [sig]
    
    def add_output_probe(self, sig):
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
