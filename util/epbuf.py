from migen import Module, ModuleTransformer
from  litex.soc.interconnect.stream import DIR_SOURCE, DIR_SINK, Endpoint, PipeReady, PipeValid

class _SkidBuffer(Module):
    def __init__(self, layout):
        self.sink = sink = Endpoint(layout)
        self.source = source = Endpoint(layout)

        self.submodules.pv = pv = PipeValid(layout)
        self.comb += self.sink.connect(pv.sink)

        self.submodules.pr = pr = PipeReady(layout)
        self.comb += [
            pv.source.connect(pr.sink),
            pr.source.connect(self.source)
        ]

# Add buffers on Endpoints (can be used to improve timings)
class InsertSkidBuffer(ModuleTransformer):
    def __init__(self, endpoint_dict):
        self.endpoint_dict = endpoint_dict

    def transform_instance(self, submodule):
        for name, direction in self.endpoint_dict.items():
            endpoint = getattr(submodule, name)
            # add buffer on sinks
            if direction == DIR_SINK:
                buf = _SkidBuffer(endpoint.description)
                submodule.submodules += buf
                setattr(submodule, name, buf.sink)
                submodule.comb += buf.source.connect(endpoint)
            # add buffer on sources
            elif direction == DIR_SOURCE:
                buf = _SkidBuffer(endpoint.description)
                submodule.submodules += buf
                submodule.comb += endpoint.connect(buf.sink)
                setattr(submodule, name, buf.source)
            else:
                raise ValueError
