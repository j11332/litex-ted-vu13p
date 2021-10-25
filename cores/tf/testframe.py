from litex.soc.interconnect import stream

def testFrameDescriptor(dw):
    _payload_layout = [
        ("data", dw),
    ]
    _param_layout = [
        ("length", 16),
    ]
    return stream.EndpointDescription(_payload_layout, _param_layout)
