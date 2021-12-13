from litex.build import xilinx
import json
import os.path

class XilinxPlatform(xilinx.XilinxPlatform):
    def __init__(self, part, _io, _connectors, toolchain="vivado"):
        xilinx.XilinxPlatform.__init__(self, part, _io, _connectors, toolchain=toolchain)
        self.tcl_ip_vars = []
        
    def create_programmer(self):
        return xilinx.VivadoProgrammer()

    def set_ip_cache_dir(self, cache_dir):
        self.toolchain.pre_synthesis_commands += [
            "# Set IP cache directory\n"
            f"config_ip_cache -import_from_project -use_cache_location {cache_dir}"
        ]
    
    def add_tcl_ip(self, ipdef, name, config):
        self.toolchain.pre_synthesis_commands += [
            "create_ip "
            f"-vlnv {ipdef}:* "
            f"-module_name {name}"
        ]
        
        ip_params_json = json.dumps(config)
        self.toolchain.pre_synthesis_commands += [
            "set_property -quiet "
            "-dict [bd::json2dict {{"
            f"{{{ip_params_json}}}"
            "}}] "
            f"[get_ips {name}]"
        ]
        
        self.toolchain.pre_synthesis_commands += [
            f"generate_target all [get_ips {name}]",
            "catch {{" f"config_ip_cache -export [get_ips -all {name}]" "}}",
            f"export_ip_user_files -of_objects [get_files [get_property IP_FILE [get_ips {name}]]] -no_script -sync -force -quiet",
            f"set {name}_run [create_ip_run -force [get_files -of_objects [get_fileset sources_1] [get_property IP_FILE [get_ips {name}]]]]"
        ]
        self.tcl_ip_vars += [name]

    def finalize_tcl_ip(self):
        tcl_runs = " ".join([f"${name}_run" for name in self.tcl_ip_vars])
        self.toolchain.pre_synthesis_commands += [
            "launch_runs -jobs 10 " f"{tcl_runs}",
            f"foreach run [list " f"{tcl_runs}]" " {{",
            "    wait_on_run $run",
            "}}"
        ]
    
    def add_source(self, filename, language=None, library=None, project=False):
        if not project:
            super().add_source(filename, language, library)
        else:
            fullpath = os.path.abspath(filename)
            self.toolchain.pre_synthesis_commands += [
                f"add_files {fullpath}"
            ]
    
    def add_sources(self, path, *filenames, language=None, library=None, project=False):
        for f in filenames:
            self.add_source(os.path.join(path, f), language, library, project)
    