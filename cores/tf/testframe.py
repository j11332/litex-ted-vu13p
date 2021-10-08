from litex.soc.interconnect import stream

def testFrameDescriptor(dw):
    _payload_layout = [
        ("data", dw),
    ]
    return stream.EndpointDescription(_payload_layout)
