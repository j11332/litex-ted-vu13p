module one_hot #(
	parameter PORTS = 2
)(
	input [$clog2(PORTS)-1:0] bin_i,
	output logic [PORTS-1:0] onehot_o 
);
	assign onehot_o = 1'b1 << bin_i;
endmodule

module i2c_mux #(
	parameter PORTS = 2
)(
	output sp_scl_i, // IIC Serial Clock Input from 3-state buffer (required)
	input sp_scl_o, // IIC Serial Clock Output to 3-state buffer (required)
	input sp_scl_t, // IIC Serial Clock Output Enable to 3-state buffer (required)
	output sp_sda_i, // IIC Serial Data Input from 3-state buffer (required)
	input sp_sda_o, // IIC Serial Data Output to 3-state buffer (required)
	input sp_sda_t, // IIC Serial Data Output Enable to 3-state buffer (required)
	input  [PORTS-1:0] mp_scl_i,
	output [PORTS-1:0] mp_scl_o,
	output [PORTS-1:0] mp_scl_t,
	input  [PORTS-1:0] mp_sda_i,
	output [PORTS-1:0] mp_sda_o,
	output [PORTS-1:0] mp_sda_t,
	input [$clog2(PORTS)-1:0] sel
);
	logic [PORTS-1:0] outmask;
	one_hot #(.PORTS(PORTS)) outmask_gen(
		.bin_i(sel),
		.onehot_o(outmask));


	assign sp_scl_i = mp_scl_i[sel];
	assign sp_sda_i = mp_sda_i[sel];

	assign mp_sda_t = ~(outmask) | {PORTS{sp_sda_t}};
	assign mp_scl_t = ~(outmask) | {PORTS{sp_scl_t}};
	assign mp_sda_o = '0;
	assign mp_scl_o = '0;
	
endmodule : i2c_mux
