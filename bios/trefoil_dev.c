#include <generated/csr.h>
#include "trefoil_dev.h"
#include "delay.h"
#include "init.h"
#ifdef CSR_SB_SI5341_O_BASE
void trefoil_clock_gen_reset(void)
{
    sb_si5341_o_out_write(0x0C);  // in_sel_0->L, syncb->H, rstb->L
	DELAY_MS(500);
	sb_si5341_o_out_write(0x3C);  // in_sel_0->L, syncb->H, rstb->H
	DELAY_MS(500);
	return;
}
// define_init_func(trefoil_clock_gen_reset);
#endif

#ifdef CSR_SB_TCA9548_BASE
void trefoil_iicio_reset(void)
{
	sb_tca9548_out_write(0x00);  // assert reset
	DELAY_MS(500);
	sb_tca9548_out_write(0x0f);  // de-assert reset
    DELAY_MS(500);
	return;
}
// define_init_func(trefoil_iicio_reset);
#endif
