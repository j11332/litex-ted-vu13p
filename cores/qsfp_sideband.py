from migen import *
from litex.soc.interconnect.csr import AutoCSR, CSRStorage, CSRStatus, CSRField, CSRConstant

class QSFPSidebandRegister(Module, AutoCSR):
    def __init__(self, pads):
        _fields_input = [
            CSRField("MODPRSL"),
            CSRField("INTL"),
        ]
        _fields_output = [
            CSRField("MODSELL", reset=1),
            CSRField("RESETL", reset=1),
            CSRField("LPMODE", reset=0),
        ]
        
        self.status = status = CSRStatus(fields=_fields_input, name="qsfp0_status")
        self.control = control = CSRStorage(fields=_fields_output, name="qsfp0_control")

        for _f in _fields_input:
            self.comb += getattr(status.fields, _f.name).eq(getattr(pads, _f.name))
        
        for _f in _fields_output:
            self.comb += getattr(pads, _f.name).eq(getattr(control.fields, _f.name))
