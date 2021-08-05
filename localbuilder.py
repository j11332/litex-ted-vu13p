from litex.soc.integration.builder import *
import os

class LocalBuilder(Builder):
    def add_software_package(self, name, src_dir=None):
        # Workaround for custom bios source
        if name == "bios":
            src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bios")

        if src_dir is None:
            src_dir = os.path.join(soc_directory, "software", name)
        
        self.software_packages.append((name, src_dir))
