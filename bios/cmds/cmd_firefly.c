// SPDX-License-Identifier: BSD-Source-Code

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#include <i2c.h>
#include <generated/csr.h>

#include "../command.h"
#include "../helpers.h"

#define I2C_SLV_ADDR_SI5341 0x77

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

	printf("device_num=%u, divider_num=%u\n", device_num, divider_num);
	printf("n_num_h=0x%03x\n", n_num_h);
	printf("n_num_l=0x%08x\n", n_num_l);
	printf("n_den=0x%08x\n", n_den);

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
