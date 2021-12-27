# Endpoint Description for Kyokko 64b/66b
def kyokkoStreamDesc(lanes=4):
    from litex.soc.interconnect.stream import EndpointDescription
    return EndpointDescription(
        [
            ("data", 64 * lanes),
            ("last_be", (64 * lanes) // 8)
        ]
    )