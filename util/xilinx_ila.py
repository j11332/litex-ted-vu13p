from argparse import ArgumentError

class XilinxILATracer:
    platform = None
    cores = dict()
    def __init__(self, platform = None):
        if platform is None and self.platform is None:
            ArgumentError("Platform is not specified.")
        
        self.platform = platform
        # Quick and dirty hack
        # Parse XDCs as TCL script
        platform.toolchain.pre_synthesis_commands += [
            "set_property FILE_TYPE TCL [get_files *.xdc -filter \"IS_GENERATED == false\"]",
            "add_files -fileset constrs_1 -norecurse gen_ila.tcl"
        ]

        platform.toolchain.additional_commands += [
            "write_debug_probe -force {build_name}.ltx"
        ]

    def add_probe(self, sig, clock, trigger=False):
        if self.cores.get(clock.duid) is None:
            clock.attr.add(('ILA_CLOCK_DUID', str(clock.duid)))
            clock.attr.add(('KEEP', 'true'))
            self.cores[clock.duid] = []
        sig.attr.add(('KEEP', 'true'))
        sig.attr.add(('MARK_DEBUG', "true"))
        sig.attr.add(('PROBE_TYPE', "DATA_AND_TRIGGER" if trigger else "DATA"))
        sig.attr.add(("DUID", str(sig.duid)))
        self.cores[clock.duid] += [(sig, "DATA_AND_TRIGGER" if trigger else "DATA")]
    
    def generate_ila(self, path):
        commands = []
        for k, v in self.cores.items():
            commands += [
                f"set ila [create_debug_core ila_{k} ila]",
                "set_property -dict {ALL_PROBE_SAME_MU true ALL_PROBE_SAME_MU_CNT "
                "1 C_ADV_TRIGGER false C_DATA_DEPTH 1024 C_EN_STRG_QUAL false "
                "C_INPUT_PIPE_STAGES 4 C_TRIGIN_EN false C_TRIGOUT_EN false}"
                f" [get_debug_cores ila_{k}]",
                "set_property port_width 1 [get_debug_ports " f"ila_{k}/clk]",
                "connect_debug_port " f"ila_{k}/clk " "[get_nets -hier -filter {" f"ILA_CLOCK_DUID=={k}" "}" "]",
            ]
            for i, tsig in enumerate(v):
                sig = tsig[0]
                get_net_cmd = "[lsort -dictionary [get_nets -hier -filter \"" f"DUID == {str(sig.duid)}" "\"]]"
                if i is not 0:
                    commands += [
                        f"create_debug_port ila_{k} probe"
                    ]
                commands += [
                    "set_property " "PROBE_TYPE " f"{tsig[1]} " f"[get_debug_ports ila_{k}/probe{i}]",
                    "set_property " "port_width " f"{len(sig)} " f"[get_debug_ports ila_{k}/probe{i}]",
                    "connect_debug_port " f"[get_debug_ports ila_{k}/probe{i}] " + get_net_cmd,
                ]
            from litex.build import tools
            import os.path
            tools.write_to_file(
                os.path.join(path, "gen_ila.tcl"),
                "\n".join(commands))