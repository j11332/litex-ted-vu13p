# Platform Utility
from litex.build.generic_platform import Subsignal, Pins, IOStandard, PlatformInfo

def diff_clk(name, id, pin_n, pin_p, iostandard = None, freq_hz = None):
    _r = [
        name, id,
        Subsignal("n", Pins(pin_n)),
        Subsignal("p", Pins(pin_p))
    ]
    if iostandard is not None:
        _r += [IOStandard(iostandard)]
    
    if freq_hz is not None:
        _r += [PlatformInfo({"freq_hz" : freq_hz})]

    return tuple(_r)

