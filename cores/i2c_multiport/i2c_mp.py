#!/usr/bin/python
from typing import TypeVar, Union
from migen import *
from migen.fhdl.specials import TSTriple, Tristate
from migen.genlib.misc import WaitTimer
from litex.soc.interconnect.csr import *
import os.path

class MuxNto1(Module):
    def __init__(self, din : Signal, douts, sel : Signal, default_state = 1):
        self.din = din
        self.douts = douts
        self.sel = sel
        self.default_state = default_state
        print(os.path.dirname(__file__))
        ###
        for i, op in enumerate(self.douts):
            self.comb += If(i == self.sel,
                            op.eq(self.din)
                        ).Else(
                            op.eq(self.default_state)
                        )

class I2CMasterMP(Module, AutoCSR):
    """I2C Master Bit-Banging

    Provides the minimal hardware to do software I2C Master bit banging.

    On the same write CSRStorage (_w), software can control:
    - SCL (I2C_SCL).
    - SDA direction and value (I2C_OE, I2C_W).

    Software get back SDA value with the read CSRStatus (_r).
    """
    pads_layout = [("scl", 1), ("sda", 1)]
    def __init__(self, platform, pads=None):
        if pads is None:
            self.port_count = 1
            pads = Record(self.pads_layout)

        self.pads = pads
        self.port_count = len(pads)

        self._w = CSRStorage(fields=[
            CSRField("scl", size=1, offset=0),
            CSRField("oe",  size=1, offset=1),
            CSRField("sda", size=1, offset=2)],
            name="w")
        self._r = CSRStatus(fields=[
            CSRField("sda", size=1, offset=0)],
            name="r")
        self._sel = CSRStorage(fields=[
            CSRField("sel", size=bits_for(self.port_count), offset=0)],
            name="sel_w")
        
        # MUX -> Tristate
        self.downstream_scl_i = Signal(self.port_count)
        self.downstream_scl_o = Signal(self.port_count)
        self.downstream_scl_t = Signal(self.port_count)
        self.downstream_sda_i = Signal(self.port_count)
        self.downstream_sda_o = Signal(self.port_count)
        self.downstream_sda_t = Signal(self.port_count)
        
        self.mux_params = dict(
            p_PORTS = self.port_count,
            # o_sp_scl_i = ,
            i_sp_scl_o = 0,
            i_sp_scl_t = self._w.fields.scl,
            o_sp_sda_i = self._r.fields.sda,
            i_sp_sda_o = 0,
            i_sp_sda_t = ~(self._w.fields.oe & ~self._w.fields.sda),
            i_mp_scl_i = self.downstream_scl_i,
            o_mp_scl_o = self.downstream_scl_o,
            o_mp_scl_t = self.downstream_scl_t,
            i_mp_sda_i = self.downstream_sda_i,
            o_mp_sda_o = self.downstream_sda_o,
            o_mp_sda_t = self.downstream_sda_t,
            i_sel = self._sel.fields.sel,
        )

        srcdir = os.path.dirname(__file__)
        platform.add_sources(srcdir, "i2c_selector.sv")
        self.connect(pads)
        
    def connect(self, pads):

        self.specials.mux = Instance("i2c_mux", **self.mux_params)
        
        for i, pad in enumerate(pads):
            # SCL
            self.specials += Tristate(
                target = pad.scl,
                o  = self.downstream_scl_o[i], # I2C uses Pull-ups, only drive low.
                oe = ~self.downstream_scl_t[i] # Drive when scl is low.
            )
                
            # SDA
            self.specials += Tristate(
                target = pad.sda,
                o  = self.downstream_sda_o[i], # I2C uses Pull-ups, only drive low.
                oe = ~self.downstream_sda_t[i], # Drive when oe and sda is low.
                i  = self.downstream_sda_i[i]
            )
