module aurora_reset_seq #(
  parameter RSTPB_ASSERT_CYCLE   = 100,       // 1us @ 100MHz
  parameter PMAINIT_ASSERT_CYCLE = 100000000, // 1s @ 100MHz
  parameter bit INSERT_CDC = 'b1
)(
  input  wire   init_clk,
  input  wire   init_clk_locked,
  input  wire   ext_reset_in,
  input  wire   are_sys_reset_in,
  output logic  done,
  output logic  are_reset_pb_out,
  output logic  are_pma_init_out
);

  logic locked_sync;
  generate
    if (INSERT_CDC) begin
      xpm_cdc_single #(
        .DEST_SYNC_FF(8),
        .INIT_SYNC_FF(0),
        .SIM_ASSERT_CHK(0),
        .SRC_INPUT_REG(0)
      ) cdc_init_clk_locked (
        .src_clk(1'b0),
        .src_in(init_clk_locked),
        .dest_clk(init_clk),
        .dest_out(locked_sync)
      );
    end else begin
      assign locked_sync = init_clk_locked;
    end
  endgenerate

  logic ext_reset_in_buf;
  always @(posedge init_clk)
    ext_reset_in_buf <= ext_reset_in;

  logic sysreset_sync;
  
  generate
    if (INSERT_CDC) begin
        xpm_cdc_single #(
          .DEST_SYNC_FF(8),
          .INIT_SYNC_FF(0),
          .SIM_ASSERT_CHK(0),
          .SRC_INPUT_REG(0)
        ) cdc_are_sysreset (
          .src_clk(1'b0),
          .src_in(are_sys_reset_in),
          .dest_clk(init_clk),
          .dest_out(sysreset_sync)
        );
    end else begin
      assign sysreset_sync = are_sys_reset_in;
    end
  endgenerate

  enum {
    SEQ_IDLE,
    SEQ_ASSERT_RSTPB,
    SEQ_ASSERT_PMAINIT,
    SEQ_NEGATE_PMAINIT,
    SEQ_NEGATE_RSTPB
  } seq_state;
  logic [31:0] assert_count;

  always_ff @(posedge init_clk) begin
    if (~locked_sync | ext_reset_in_buf)
      assert_count <= 32'd0;
    else if (seq_state == SEQ_ASSERT_RSTPB) begin
      if (assert_count == RSTPB_ASSERT_CYCLE)
        assert_count <= 32'd0;
      else
        assert_count <= assert_count + 32'd1;
    end
    else if (seq_state == SEQ_ASSERT_PMAINIT) begin
      if (assert_count == PMAINIT_ASSERT_CYCLE)
        assert_count <= 32'd0;
      else
        assert_count <= assert_count + 32'd1;
    end
    else
      assert_count <= assert_count;
  end

  always_ff @(posedge init_clk) begin
    if (~locked_sync | ext_reset_in_buf)
      seq_state <= SEQ_IDLE;
    else if (seq_state == SEQ_IDLE)
      seq_state <= SEQ_ASSERT_RSTPB;
    else if (seq_state == SEQ_ASSERT_RSTPB) begin
      if (assert_count == RSTPB_ASSERT_CYCLE)
        seq_state <= SEQ_ASSERT_PMAINIT;
      else
        seq_state <= seq_state;
    end
    else if (seq_state == SEQ_ASSERT_PMAINIT) begin
      if (assert_count == PMAINIT_ASSERT_CYCLE)
        seq_state <= SEQ_NEGATE_PMAINIT;
      else
        seq_state <= seq_state;
    end
    else if (seq_state == SEQ_NEGATE_PMAINIT) begin
      if (sysreset_sync)
        seq_state <= SEQ_NEGATE_RSTPB;
      else
        seq_state <= seq_state;
    end
    else if (seq_state == SEQ_NEGATE_RSTPB)
      seq_state <= seq_state;
    else
      seq_state <= SEQ_IDLE;
  end

  always_ff @(posedge init_clk) begin
    done <= (seq_state == SEQ_NEGATE_RSTPB);
    are_reset_pb_out <= |seq_state[1:0];  // SEQ_ASSERT_RSTPB, SEQ_ASSERT_PMAINIT, SEQ_NEGATE_PMAINIT
    are_pma_init_out <= (seq_state == SEQ_ASSERT_PMAINIT);
  end

endmodule
