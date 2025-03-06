`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
//
// Modulation generator.
// Creates harmonic functions of 4*WFMLEN data length. You can choose how many clock
// ticks last each data value with hp input.
//
// Creates square signals, whose half period is set by using sqp input.
//
//////////////////////////////////////////////////////////////////////////////////



//(* keep_hierarchy = "yes" *)
module gen_mod_h
#( parameter WFMLEN = 13'd1250 ) //630 with original waveform
(
    input clk,rst,
    input           [13-1:0] phase,    // Phase control
    input           [14-1:0] hp,   // Harmonic period control
    output signed   [14-1:0] sin_ref, sin_1f, sin_2f, sin_3f,
    output signed   [14-1:0] cos_ref, cos_1f, cos_2f, cos_3f,
    output                   harmonic_trig//, square_trig
);
    localparam H = 2'd1; //frequency multiplier
    localparam WB = $clog2(WFMLEN+1);

    reg  [13-1:0] phase_b;
    wire          cnt_next_zero;


    //divisor
    wire tau_tick;
    wire tau_tick_cnt_equal_hp;
    reg  [14-1:0] tau_tick_cnt;
    wire [15-1:0] tau_tick_cnt_next;


    reg signed [14-1:0] memory_cos_r [WFMLEN:0]; // vector for amplitude value
    initial
    begin
        $readmemb("data_cos_ss.dat", memory_cos_r); // read memory binary code from data_cos.dat
    end

    /* Frequency divider  --------------------------------------------*/

    always @(posedge clk)
	if (rst)
		tau_tick_cnt <= 0; // {N{1b'0}}
	else
		tau_tick_cnt <= tau_tick_cnt_next[14-1:0];

    assign tau_tick_cnt_equal_hp = (tau_tick_cnt==hp) ;
    assign tau_tick_cnt_next = tau_tick_cnt_equal_hp ? 14'b0 : tau_tick_cnt + 14'b001;
    assign tau_tick = (hp==14'b0) ? 1'b1 : tau_tick_cnt_equal_hp ;

    /*--------------------------------------------------------------------*/


    // counter is synchronized with gen_ramp signal

    // for sin and cos:  cnt , r_addr
    reg  [WB-1:0]  cnt ;
    wire [WB-1:0]  cnt_next ;
    wire [WB-1:0]  cnt_rev ;
    reg  [WB+1:0]  cntu ;
    wire [WB+1:0]  cntu_next ;
    wire [WB-1:0]  r_addrc ;
    wire [WB-1:0]  r_addrs ;

    reg  [ 2-1:0]  quad_bit ;
    wire [ 2-1:0]  quad_bit_next ;
    wire           quad_add;

    always @(posedge clk)
        if (rst)
        begin
            cnt           <=   {WB{1'b0}};
            quad_bit      <=   2'b0;
            cntu          <=   {(WB+2){1'b0}};
            phase_b       <=   (4*WFMLEN-1);
        end
        else
        begin
            cnt       <=  cnt_next;
            quad_bit  <=  quad_bit_next;
            cntu      <=  cntu_next;
            if(phase==13'b0)
                phase_b  <= (4*WFMLEN-1) ;
            else
                phase_b  <= phase - 13'b1 ;
        end
    assign quad_add       = (cnt >= (WFMLEN-H));
    assign quad_bit_next  = quad_bit + (tau_tick&quad_add) ;
    assign cnt_next       = tau_tick ? cnt + H - (quad_add ? WFMLEN : 0) :  cnt;
    assign cnt_rev        = WFMLEN - cnt;
    assign r_addrc        = quad_bit[0] ? cnt_rev : cnt;
    assign r_addrs        = quad_bit[0] ? cnt : cnt_rev;

    assign cnt_next_zero  = (quad_bit==2'b11)&(cnt==(WFMLEN-H))&tau_tick ;
    assign cntu_next      = cnt_next_zero ? {(WB+2){1'b0}} :  cntu + tau_tick  ;

    assign  harmonic_trig = cnt_next_zero ;


    // for cos_1f :  cnt1 , r_addr1
    reg  [WB-1:0]  cnt1 ;
    wire [WB-1:0]  cnt1_next ;
    wire [WB-1:0]  cnt1_rev ;
    reg  [ 2-1:0]  quad_bit1 ;
    wire [ 2-1:0]  quad_bit1_next ;
    wire           quad_add1;
    wire [WB-1:0]  r_addr1c;
    wire [WB-1:0]  r_addr1s;

    always @(posedge clk)
        if (rst)
        begin
            cnt1      <=   {WB{1'b0}};
            quad_bit1 <=   2'b0;
        end
        else
        begin
            cnt1      <=  cnt1_next;
            quad_bit1 <=  quad_bit1_next;
        end
    assign quad_add1      = (cnt1 >= (WFMLEN-H));
    assign quad_bit1_next = ( cntu == phase_b ) ? 2'b00  : quad_bit1 + (tau_tick&quad_add1) ;
    assign cnt1_next      = ( cntu == phase_b ) ? {WB{1'b0}}  :
                            tau_tick ? cnt1 + H - (quad_add1 ? WFMLEN : 0) :  cnt1;
    assign cnt1_rev       = WFMLEN - cnt1;
    assign r_addr1c       = quad_bit1[0] ? cnt1_rev : cnt1;
    assign r_addr1s       = quad_bit1[0] ? cnt1 : cnt1_rev;

    // for cos_2f :  cnt2 , r_addr2
    reg  [WB-1:0]  cnt2 ;
    wire [WB-1:0]  cnt2_next ;
    wire [WB-1:0]  cnt2_rev ;
    reg  [ 2-1:0]  quad_bit2 ;
    wire [ 2-1:0]  quad_bit2_next ;
    wire           quad_add2;
    wire [WB-1:0]  r_addr2c;
    wire [WB-1:0]  r_addr2s;

    always @(posedge clk)
        if (rst)
        begin
            cnt2      <=   {WB{1'b0}};
            quad_bit2 <=   2'b0;
        end
        else
        begin
            cnt2      <=  cnt2_next;
            quad_bit2 <=  quad_bit2_next;
        end
    assign quad_add2      = (cnt2 >= (WFMLEN-2*H));
    assign quad_bit2_next = ( cntu == phase_b ) ? 2'b00  : quad_bit2 + (tau_tick&quad_add2) ;
    assign cnt2_next      = ( cntu == phase_b ) ? {WB{1'b0}}  :
                            tau_tick ? cnt2 + 2*H - (quad_add2 ? WFMLEN : 0) :  cnt2;
    assign cnt2_rev       = WFMLEN - cnt2;
    assign r_addr2c       = quad_bit2[0] ? cnt2_rev : cnt2;
    assign r_addr2s       = quad_bit2[0] ? cnt2 : cnt2_rev;

    // for cos_3f :  cnt3 , r_addr3
    reg  [WB-1:0]  cnt3 ;
    wire [WB-1:0]  cnt3_next ;
    wire [WB-1:0]  cnt3_rev ;
    reg  [ 2-1:0]  quad_bit3 ;
    wire [ 2-1:0]  quad_bit3_next ;
    wire           quad_add3;
    wire [WB-1:0]  r_addr3c;
    wire [WB-1:0]  r_addr3s;

    always @(posedge clk)
        if (rst)
        begin
            cnt3      <=   {WB{1'b0}};
            quad_bit3 <=   2'b0;
        end
        else
        begin
            cnt3      <=  cnt3_next;
            quad_bit3 <=  quad_bit3_next;
        end
    assign quad_add3      = (cnt3 >= (WFMLEN-3*H));
    assign quad_bit3_next = ( cntu == phase_b ) ? 2'b00  : quad_bit3 + (tau_tick&quad_add3) ;
    assign cnt3_next      = ( cntu == phase_b ) ? {WB{1'b0}}  :
                            tau_tick ? cnt3 + 3*H - (quad_add3 ? WFMLEN : 0) :  cnt3;
    assign cnt3_rev       = WFMLEN - cnt3;
    assign r_addr3c       = quad_bit3[0] ? cnt3_rev : cnt3;
    assign r_addr3s       = quad_bit3[0] ? cnt3 : cnt3_rev;


    assign cos_ref  =  quad_bit[1]^quad_bit[0]     ?  $signed(-memory_cos_r[r_addrc])  : memory_cos_r[r_addrc] ;
    assign sin_ref  =  quad_bit[1]                 ?  $signed(-memory_cos_r[r_addrs])  : memory_cos_r[r_addrs] ;
    assign cos_1f   =  quad_bit1[1]^quad_bit1[0]   ?  $signed(-memory_cos_r[r_addr1c]) : memory_cos_r[r_addr1c] ;
    assign sin_1f   =  quad_bit1[1]                ?  $signed(-memory_cos_r[r_addr1s]) : memory_cos_r[r_addr1s] ;
    assign cos_2f   =  quad_bit2[1]^quad_bit2[0]   ?  $signed(-memory_cos_r[r_addr2c]) : memory_cos_r[r_addr2c] ;
    assign sin_2f   =  quad_bit2[1]                ?  $signed(-memory_cos_r[r_addr2s]) : memory_cos_r[r_addr2s] ;
    assign cos_3f   =  quad_bit3[1]^quad_bit3[0]   ?  $signed(-memory_cos_r[r_addr3c]) : memory_cos_r[r_addr3c] ;
    assign sin_3f   =  quad_bit3[1]                ?  $signed(-memory_cos_r[r_addr3s]) : memory_cos_r[r_addr3s] ;



endmodule

/**
  * Notes to write documentation
  * When sqp == 0 we are in Harmonic mode --> we use harmonic functions to modulate
    * out_sin / out_cos outputs the sine and cosine functions
    * out_sin2, out_sin3, out_sinf  outputs sine funtions with phase relation to out_sin
    * sq_ref  outputs sgn(out_sin)  --> (1 for positive, 0 for negative)
    * sq_quad outputs sgn(out_cos)  --> (1 for positive, 0 for negative)
    * sq_phas outputs sgn(out_sinf) --> (1 for positive, 0 for negative)
    * phase control sets the number of clk2 clock ticks to wait before counter reset
    * hp sets the clk ticks number to wait before clk2 clock advance one tick
      * It's a frequency divider




    | out_sin
    |       ****                              ****
    |    ***    ***                        ***    ***
    |  **          **                    **          **
    | *              *                  *              *
    |*----------------*----------------*----------------*
    |                  *              *
    |                   **          **
    |                     ***    ***
    |                        ****

    | out_sinf
    |            ****                              ****
    |         ***    ***                        ***    ***
    |       **          **                    **          **
    |      *              *                  *              *
    |-----*----------------*----------------*----------------*
    |    *|                 *              *
    |  **  \                 **          **
    |**     \                  ***    ***
    |        phase                ****


*/
