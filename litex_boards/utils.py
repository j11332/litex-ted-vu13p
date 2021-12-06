# Platform Utility
from litex.build.generic_platform import Subsignal

class GTSubSignal(Subsignal):
    def __init__(self, name, gt_loc, *constraints):
        self.gt_loc = gt_loc
        Subsignal.__init__(self, name, constraints=constraints)

    def get_gt_loc(self):
        return self.gt_loc
