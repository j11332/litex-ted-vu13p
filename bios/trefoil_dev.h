#include <generated/csr.h>
#ifndef _TREFOIL_DEV_H

#ifdef CSR_SB_SI5341_O_BASE
void trefoil_clock_gen_reset(void);
#endif

#ifdef CSR_SB_TCA9548_BASE
void trefoil_iicio_reset(void);
#endif

#endif /* _TREFOIL_DEV_H */