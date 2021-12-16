#include <generated/csr.h>
#include "bootcmd.h"

const char *bootcmds = {
#if defined( CSR_SB_SI5341_O_BASE ) && defined( CSR_SB_TCA9548_BASE )
  "reset_si5341\n"  // reset external PLL IC
  "set_si5341_n_divider 0 0 0x015 0x80000000 0x84000000\n"  // set GTY 1xx RefClk 161.1328125MHz
  "set_si5341_n_divider 1 0 0x015 0x80000000 0x84000000\n"  // set GTY 2xx RefClk 161.1328125MHz
  "reset_tca9548\n"  // reset I2C MUX
  "reset_firefly\n"  // reset FireFly optical module
#else
  ""
#endif
};

static int cmd_cur = 0;

int getbootcmd(char *buf, int len)
{
  int i;
  for (i = 0; i < len; i++) {
    if (bootcmds[i+cmd_cur] == '\n') {
      cmd_cur += i + 1;
      buf[i] = '\0';
      return i;
    } else if (bootcmds[i+cmd_cur] == '\0') {
      return 0;
    }
    buf[i] = bootcmds[i+cmd_cur];
  }

  return 0;
}
