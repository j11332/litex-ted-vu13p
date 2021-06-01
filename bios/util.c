#include "util.h"

// GTY num to i2c_mux / tca9548_reg calculate
int gty2mux(uint8_t gty_num, uint8_t *i2c_mux, uint8_t *tca9548_reg)
{
	if (!(gty_num >= 120 && gty_num <= 135) && !(gty_num >= 220 && gty_num <= 223) && !(gty_num >= 228 && gty_num <= 235)) {
		return 1;
	}

	if (gty_num <= 127) {
		*i2c_mux = 7;
		*tca9548_reg = 0x01 << (gty_num - 120);
	} else if (gty_num <= 135) {
		*i2c_mux = 8;
		*tca9548_reg = 0x01 << (gty_num - 128);
	} else if (gty_num <= 223) {
		*i2c_mux = 9;
		*tca9548_reg = 0x01 << (gty_num - 220);
	} else {
		*i2c_mux = 10;
		*tca9548_reg = 0x01 << (gty_num - 228);
	}

	return 0;
}
