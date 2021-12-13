# Platform Utility
from litex.build.generic_platform import Subsignal, Pins, IOStandard

class GTSubSignal(Subsignal):
    def __init__(self, name, gt_loc, *constraints):
        self.gt_loc = gt_loc
        Subsignal.__init__(self, name, constraints=constraints)

    def get_gt_loc(self):
        return self.gt_loc

def diff_clk(name, id, pin_n, pin_p, iostandard = None):
    _r = (
        name, id,
        Subsignal("n", Pins(pin_n)),
        Subsignal("p", Pins(pin_p))
    )
    if iostandard is not None:
        _r += tuple([IOStandard(iostandard)])

    return _r
