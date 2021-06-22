import os
from migen import *

class USPGTY(Module):
    def __init__(self, platform, pads):
        self.platform = platform
        self.pads = pads
    
    def add_sources(self, path, filename):
        self.platform.add_ip(os.path.join(path, filename))
    