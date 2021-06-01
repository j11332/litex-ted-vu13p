// SPDX-License-Identifier: BSD-Source-Code

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#include <i2c.h>
#include <generated/csr.h>

#include "../util.h"
#include "../command.h"
#include "../helpers.h"

#define I2C_SLV_ADDR_TCA9555 0x20
#define I2C_SLV_ADDR_TCA9548 0x70
#define I2C_SLV_ADDR_SI5341 0x77
#define I2C_SLV_ADDR_FIREFLY 0x50

#define DELAY_MS(n) cdelay((n)*(CONFIG_CLOCK_FREQUENCY/4000))

static inline void cdelay(int i)
{
	while(i > 0) {
		__asm__ volatile(CONFIG_CPU_NOP);
		i--;
	}
}

/**
 * Command "reset_si5341"
 *
 * Reset all SI5341
 *
 */
#ifdef CSR_SB_SI5341_O_BASE
static void reset_si5341_handler(int nb_params, char **params)
{
	sb_si5341_o_out_write(0x0C);  // in_sel_0->L, syncb->H, rstb->L
	DELAY_MS(500);
	sb_si5341_o_out_write(0x3C);  // in_sel_0->L, syncb->H, rstb->H
	return;
}

define_command(reset_si5341, reset_si5341_handler, "Reset all SI5341", FIREFLY_CMDS);
#endif

/**
 * Command "set_si5341_n_divider"
 *
 * Set N divider of SI5341
 *
 */
#ifdef CSR_I2C_SEL_W_ADDR
static void set_si5341_n_divider_handler(int nb_params, char **params)
{
	char *c;
	uint8_t device_num, divider_num, reg_addr, reg_offset;
	uint32_t n_num_h, n_num_l, n_den;
	uint8_t data[6];
	int i;

	if (nb_params != 5) {
		printf("set_si5341_n_divider <device num> <divider num> <N numerator higher 12-bit> <N numerator lower 32-bit> <N denominator>");
		return;
	}

	device_num = strtoul(params[0], &c, 0);
	if ((*c != 0) || (device_num > 1)) {
		printf("Incorrect device number (0 or 1)");
		return;
	}

	divider_num = strtoul(params[1], &c, 0);
	if ((*c != 0) || (divider_num > 5)) {
		printf("Incorrect divider number (0 - 4)");
		return;
	}

	n_num_h = strtoul(params[2], &c, 0);
	if (*c != 0) {
		printf("Incorrect N numerator higher 12-bit");
		return;
	}

	n_num_l = strtoul(params[3], &c, 0);
	if (*c != 0) {
		printf("Incorrect N numerator lower 32-bit");
		return;
	}

	n_den = strtoul(params[4], &c, 0);
	if (*c != 0) {
		printf("Incorrect N denominator (32-bit)");
		return;
	}

	i2c_sel_w_sel_write(device_num + 11);  // i2c_mux set to 11 or 12

	// set page register to 0x03
	reg_addr = 0x01;
	data[0] = 0x03;
	if (!i2c_write(I2C_SLV_ADDR_SI5341, reg_addr, data, 1)) {
		goto i2c_w_err;
	}

	reg_offset = divider_num * 11;

	// set divider N numerator
	reg_addr = 0x02 + reg_offset;
	for (i = 0; i < 4; i++) {
		data[i] = (n_num_l >> (i * 8)) & 0xff;
	}
	data[4] = n_num_h & 0xff;
	data[5] = (n_num_h >> 8) & 0x0f;
	if (!i2c_write(I2C_SLV_ADDR_SI5341, reg_addr, data, 6)) {
		goto i2c_w_err;
	}

	// set divider N denominator
	reg_addr = 0x08 + reg_offset;
	for (i = 0; i < 4; i++) {
		data[i] = (n_den >> (i * 8)) & 0xff;
	}
	if (!i2c_write(I2C_SLV_ADDR_SI5341, reg_addr, data, 4)) {
		goto i2c_w_err;
	}

	// update divider N
	reg_addr = 0x0c + reg_offset;
	data[0] = 0x01;
	if (!i2c_write(I2C_SLV_ADDR_SI5341, reg_addr, data, 1)) {
		goto i2c_w_err;
	}

	return;

i2c_w_err:
	printf("Error during I2C write");
	return;
}

define_command(set_si5341_n_divider, set_si5341_n_divider_handler, "Set N divider of SI5341", FIREFLY_CMDS);
#endif

/**
 * Command "get_si5341_n_divider"
 *
 * Get N divider of SI5341
 *
 */
#ifdef CSR_I2C_SEL_W_ADDR
static void get_si5341_n_divider_handler(int nb_params, char **params)
{
	char *c;
	uint8_t device_num, divider_num, reg_addr, reg_offset;
	uint32_t n_num_h = 0, n_num_l = 0, n_den = 0;
	uint8_t data[6];
	int i;

	if (nb_params != 2) {
		printf("get_si5341_n_divider <device num> <divider num>");
		return;
	}

	device_num = strtoul(params[0], &c, 0);
	if ((*c != 0) || (device_num > 1)) {
		printf("Incorrect device number (0 - 1)");
		return;
	}

	divider_num = strtoul(params[1], &c, 0);
	if ((*c != 0) || (divider_num > 5)) {
		printf("Incorrect divider number (0 - 4)");
		return;
	}

	reg_offset = divider_num * 11;

	i2c_sel_w_sel_write(device_num + 11);  // i2c_mux set to 11 or 12

	// set page register to 0x03
	reg_addr = 0x01;
	data[0] = 0x03;
	if (!i2c_write(I2C_SLV_ADDR_SI5341, reg_addr, data, 1)) {
		goto i2c_w_err;
	}

	// get divider N numerator
	reg_addr = 0x02 + reg_offset;
	if (!i2c_read(I2C_SLV_ADDR_SI5341, reg_addr, data, 6, true)) {
		goto i2c_r_err;
	}
	for (i = 3; i >= 0; i--) {
		n_num_l = (n_num_l << 8) | (data[i] & 0xff);
	}
	n_num_h = ((data[5] & 0x0f) << 8) | (data[4] & 0xff);

	// get divider N denominator
	reg_addr = 0x08 + reg_offset;
	if (!i2c_read(I2C_SLV_ADDR_SI5341, reg_addr, data, 4, true)) {
		goto i2c_r_err;
	}
	for (i = 3; i >= 0; i--) {
		n_den = (n_den << 8) | (data[i] & 0xff);
	}

	printf("device_num = %u, divider_num=%u\n", device_num, divider_num);
	printf("n_num_h = 0x%03x\n", n_num_h);
	printf("n_num_l = 0x%08x\n", n_num_l);
	printf("n_den = 0x%08x\n", n_den);

	return;

i2c_w_err:
	printf("Error during I2C write");
	return;

i2c_r_err:
	printf("Error during I2C read");
	return;
}

define_command(get_si5341_n_divider, get_si5341_n_divider_handler, "Get N divider of SI5341", FIREFLY_CMDS);
#endif

/**
 * Command "reset_tca9548"
 *
 * Reset all TCA9548
 *
 */
#ifdef CSR_SB_TCA9548_BASE
static void reset_tca9548_handler(int nb_params, char **params)
{
	sb_tca9548_out_write(0x00);  // assert reset
	DELAY_MS(500);
	sb_tca9548_out_write(0x0f);  // de-assert reset
	return;
}

define_command(reset_tca9548, reset_tca9548_handler, "Reset all TCA9548", FIREFLY_CMDS);
#endif

/**
 * Command "reset_firefly"
 *
 * Reset all FireFly modules
 *
 */
#ifdef CSR_I2C_SEL_W_ADDR
static void reset_firefly_handler(int nb_params, char **params)
{
  	int i;
	uint8_t reg_addr, data;

	for (i = 0; i < 7; i++) {
		i2c_sel_w_sel_write(i);  // set i2c_mux

		// set I/O direction
		reg_addr = 0x06;
		data = 0xaa;  // RESET_L->output, INT_L->input, SELECT_L->output, PRESENTL->input
		if (!i2c_write(I2C_SLV_ADDR_TCA9555, reg_addr, &data, 1)) {
			goto i2c_w_err;
		}
		reg_addr = 0x07;
		if (!i2c_write(I2C_SLV_ADDR_TCA9555, reg_addr, &data, 1)) {
			goto i2c_w_err;
		}

		// assert FireFly reset
		reg_addr = 0x02;
		data = 0xaa;  // RESET_L->L, SELECT_L->L
		if (!i2c_write(I2C_SLV_ADDR_TCA9555, reg_addr, &data, 1)) {
			goto i2c_w_err;
		}
		reg_addr = 0x03;
		if (!i2c_write(I2C_SLV_ADDR_TCA9555, reg_addr, &data, 1)) {
			goto i2c_w_err;
		}
	}

	DELAY_MS(500);

	for (i = 0; i < 7; i++) {
		i2c_sel_w_sel_write(i);  // set i2c_mux

		// de-assert FireFly reset
		reg_addr = 0x02;
		data = 0xbb;  // RESET_L->H, SELECT_L->L
		if (!i2c_write(I2C_SLV_ADDR_TCA9555, reg_addr, &data, 1)) {
			goto i2c_w_err;
		}
		reg_addr = 0x03;
		if (!i2c_write(I2C_SLV_ADDR_TCA9555, reg_addr, &data, 1)) {
			goto i2c_w_err;
		}
	}

	return;

i2c_w_err:
	printf("Error during I2C write");
	return;
}

define_command(reset_firefly, reset_firefly_handler, "Reset all FireFly modules", FIREFLY_CMDS);
#endif

/**
 * Command "i2c_write_firefly"
 *
 * i2c_write for FireFly modules
 *
 */
#ifdef CSR_I2C_SEL_W_ADDR
static void i2c_write_firefly_handler(int nb_params, char **params)
{
	int i;
	char *c;
	uint8_t data[32];
	uint8_t gty_num, i2c_mux, tca9548_reg, reg_addr, data_len;

	if (nb_params < 2) {
		printf("i2c_write_firefly <GTY number> <reg addr> [<data>, ...]");
		return;
	}

	gty_num = strtoul(params[0], &c, 0);
	if ((*c != 0) || gty2mux(gty_num, &i2c_mux, &tca9548_reg)) {
		printf("Incorrect GTY number (120-135, 220-223, 228-235)");
		return;
	}

	reg_addr = strtoul(params[1], &c, 0);
	if (*c != 0) {
		printf("Incorrect register address");
		return;
	}

	data_len = nb_params - 2;

	if (data_len > sizeof(data)) {
		printf("Max data length is %zu", sizeof(data));
		return;
	}

	for (i = 0; i < data_len; i++) {
		data[i] = strtoul(params[i + 2], &c, 0);
		if (*c != 0) {
			printf("Incorrect value of data %d", i);
			return;
		}
	}

	i2c_sel_w_sel_write(i2c_mux);  // set i2c_mux

  	// set TCA9548 selector
	if (!i2c_write(I2C_SLV_ADDR_TCA9548, tca9548_reg, 0, 0)) {
		goto i2c_w_err;
	}

	// i2c_write to FireFly module
	if (!i2c_write(I2C_SLV_ADDR_FIREFLY, reg_addr, data, data_len)) {
		goto i2c_w_err;
	}

	return;

i2c_w_err:
	printf("Error during I2C write");
	return;
}

define_command(i2c_write_firefly, i2c_write_firefly_handler, "i2c_write for FireFly modules", FIREFLY_CMDS);
#endif

/**
 * Command "i2c_read_firefly"
 *
 * i2c_read for FireFly modules
 *
 */
#ifdef CSR_I2C_SEL_W_ADDR
static void i2c_read_firefly_handler(int nb_params, char **params)
{
	char *c;
	int len = 1;
	uint8_t buf[256];
	uint8_t gty_num, i2c_mux, tca9548_reg, reg_addr;

	if (nb_params < 2) {
		printf("i2c_read_firefly <GTY number> <reg addr> [<len>]");
		return;
	}

	gty_num = strtoul(params[0], &c, 0);
	if ((*c != 0) || gty2mux(gty_num, &i2c_mux, &tca9548_reg)) {
		printf("Incorrect GTY number (120-135, 220-223, 228-235)");
		return;
	}

	reg_addr = strtoul(params[1], &c, 0);
	if (*c != 0) {
		printf("Incorrect register address");
		return;
	}

	if (nb_params > 2) {
		len = strtoul(params[2], &c, 0);
		if (*c != 0) {
			printf("Incorrect data length");
			return;
		}
		if (len > sizeof(buf)) {
			printf("Max data count is %zu", sizeof(buf));
			return;
		}
	}

	i2c_sel_w_sel_write(i2c_mux);  // set i2c_mux

	// set TCA9548 selector
	if (!i2c_write(I2C_SLV_ADDR_TCA9548, tca9548_reg, 0, 0)) {
		printf("Error during I2C write");
		return;
	}

	// i2c_read from FireFly module
	if (!i2c_read(I2C_SLV_ADDR_FIREFLY, reg_addr, buf, len, true)) {
		printf("Error during I2C read");
		return;
	}

	dump_bytes((unsigned int *) buf, len, reg_addr);
}

define_command(i2c_read_firefly, i2c_read_firefly_handler, "i2c_read for FireFly modules", FIREFLY_CMDS);
#endif
