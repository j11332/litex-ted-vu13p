from migen import ModuleTransformer, Signal
from litex.soc.interconnect.stream import DIR_SINK, DIR_SOURCE, DIR_M_TO_S, DIR_S_TO_M

class EP2AXI(ModuleTransformer):
    """Endpoint to AXI Stream
    Parameter
    --------
    endpoint_dict : dict
        Key: Name of endpoint
        Value: Direction (DIR_SOURCE, DIR_SINK)

    Example
    --------
    >>> mod = stream.SyncFIFO()
    >>> _map = {
    ...     "source" : DIR_SOURCE,
    ...     "sink"   : DIR_SINK,
    ... }
    >>> mod = EP2AXI(_map)(mod)
    """

    def __init__(self, endpoint_dict):
        self.endpoint_dict = endpoint_dict

    def transform_instance(self, submodule):
        for ep_name, direction in self.endpoint_dict.items():
            endpoint = getattr(submodule, ep_name)
            try:
                ios = submodule.ios
            except:
                ios = []
                setattr(submodule, "ios", ios)

            prefix = "_s_axis_t" if direction == DIR_SINK else "_m_axis_t"
            _map = [
                ("valid", DIR_M_TO_S),
                ("ready", DIR_S_TO_M),
                ("last",  DIR_M_TO_S),
                ("data",  DIR_M_TO_S),
            ]

            for sn, _dir in _map:
                ss = getattr(endpoint, sn)
                ps = Signal.like(ss, name = endpoint.name + prefix + sn)
                if direction == DIR_SINK:
                    submodule.comb += ss.eq(ps) if _dir == DIR_M_TO_S else ps.eq(ss)
                else:
                    submodule.comb += ss.eq(ps) if _dir == DIR_S_TO_M else ps.eq(ss)
                ios.append(ps)
            
            submodule.ios = ios

