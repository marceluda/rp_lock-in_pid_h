`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
//
// Modulation generator.
// Creates harmonic functions of 2520 data length. You can choose how many clock
// ticks last each data value with hp input.
//
// Creates square signals, whose half period is set by using sqp input.
//
//////////////////////////////////////////////////////////////////////////////////

//(* keep_hierarchy = "yes" *)
module gen_mod_h
(
    input clk,rst,
    input           [12-1:0] phase,    // Phase control
    input           [32-1:0] phase_sq, // Phase control
    input           [14-1:0] hp,   // Harmonic period control
    output signed   [14-1:0] sin_ref, //sin_1f, sin_2f, sin_3f,
    output signed   [14-1:0] cos_ref, cos_1f, cos_2f, cos_3f,
    output          [12-1:0] cntu_w,
    output                   harmonic_trig//, square_trig
);


    reg  [12-1:0] phase_b;
    wire          cnt_next_zero;


    //divisor
    wire tau_tick;
    wire tau_tick_cnt_equal_hp;
    reg  [14-1:0] tau_tick_cnt;
    wire [15-1:0] tau_tick_cnt_next;


    reg signed [14-1:0] memory_sin_r [630-1:0]; // vector for amplitude value
    initial
    begin
        $readmemb("data_sin_ss.dat", memory_sin_r); // read memory binary code from data_sin.dat
    end

    reg signed [14-1:0] memory_cos_r [630-1:0]; // vector for amplitude value
    initial
    begin
        $readmemb("data_cos_ss.dat", memory_cos_r); // read memory binary code from data_cos.dat
    end


    reg signed [14-1:0] memory_cos1_r [630-1:0]; // vector for amplitude value
    initial
    begin
        $readmemb("data_cos_ss.dat", memory_cos1_r); // read memory binary code from data_sin.dat
    end

    reg signed [14-1:0] memory_cos2_r [315-1:0]; // vector for amplitude value
    initial
    begin
        $readmemb("data_cos2_ss.dat", memory_cos2_r); // read memory binary code from data_sin.dat
    end

    reg signed [14-1:0] memory_cos3_r [210-1:0]; // vector for amplitude value
    initial
    begin
        $readmemb("data_cos3_ss.dat", memory_cos3_r); // read memory binary code from data_sin.dat
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

    // read address engine *****************************************************************
    // for sin and cos:  cnt , r_addr
    reg  [10-1:0]  cnt ;
    wire [11-1:0]  cnt_next ;
    reg  [12-1:0]  cntu ;
    wire [13-1:0]  cntu_next ;

    assign cntu_w = cntu; // LOLO

    reg  [ 2-1:0]  quad_bit ;
    wire [ 3-1:0]  quad_bit_next ;
    wire           quad_add;

    always @(posedge clk)
        if (rst)
        begin
            cnt           <=   10'b0    ;
            quad_bit      <=    2'b0    ;
            cntu          <=   12'b0    ;
            phase_b       <=   12'd2519 ;
            //cnt_next_zero <=    1'b0;
        end
        else
        begin
            cnt       <=  cnt_next[10-1:0]  ;
            quad_bit  <=  quad_bit_next     ;
            cntu      <=  cntu_next[12-1:0] ;
            if(phase==12'b0)
                phase_b  <= 12'd2519 ;
            else
                phase_b  <= phase[12-1:0] - 12'b1 ;
        end

    assign quad_add       = (cnt==10'd629 & quad_bit==2'b00 ) |
                            (cnt==10'd000 & quad_bit==2'b01 ) |
                            (cnt==10'd629 & quad_bit==2'b10 ) |
                            (cnt==10'd000 & quad_bit==2'b11 )   ;

    assign quad_bit_next  = quad_add ? quad_bit + tau_tick : quad_bit ;

    assign cnt_next       = quad_add    ? cnt   :
                            quad_bit[0] ? cnt - tau_tick  :  cnt + tau_tick  ;
    assign cnt_next_zero  = (quad_bit==2'b11)&(cnt==10'd000)&tau_tick ;
    assign cntu_next      = cnt_next_zero ? 12'b0 :  cntu + tau_tick  ;

    assign  harmonic_trig = cnt_next_zero ;


    // read address engine *****************************************************************
    // for sin1f :  cnt1 , r_addr1
    reg  [10-1:0]  cnt1 ;
    wire [11-1:0]  cnt1_next ;
    reg  [ 2-1:0]  quad_bit1 ;
    wire [ 3-1:0]  quad_bit1_next ;
    wire           quad_add1;

    always @(posedge clk)
        if (rst)
        begin
            cnt1      <=   10'b0   ;
            quad_bit1 <=    2'b0   ;
        end
        else
        begin
            cnt1       <=  cnt1_next[10-1:0] ;
            quad_bit1  <=  quad_bit1_next      ;
        end

    assign quad_add1      = (cnt1==10'd629 & quad_bit1==2'b00 ) |
                            (cnt1==10'd000 & quad_bit1==2'b01 ) |
                            (cnt1==10'd629 & quad_bit1==2'b10 ) |
                            (cnt1==10'd000 & quad_bit1==2'b11 )   ;

    //assign quad_bit1_next = quad_add1 ? quad_bit1 + tau_tick : quad_bit1 ;
    assign quad_bit1_next = ( cntu == phase_b ) ? 2'b00  : quad_bit1 + (tau_tick&quad_add1) ;

    assign cnt1_next      = ( cntu == phase_b ) /*| ( cnt_next_zero & phase==12'b0 ) */? 10'b0   :
                            quad_add1    ? cnt1             :
                            quad_bit1[0] ? cnt1 - tau_tick  :  cnt1 + tau_tick  ;



    // read address engine *****************************************************************
    // for sin2f :  cnt2 , r_addr2
    reg  [ 9-1:0]  cnt2 ;
    wire [10-1:0]  cnt2_next ;
    reg  [ 2-1:0]  quad_bit2 ;
    wire [ 3-1:0]  quad_bit2_next ;
    wire           quad_add2;
    //wire [ 9-1:0]  r_addr2;

    always @(posedge clk)
        if (rst)
        begin
            cnt2      <=    9'b0   ;
            quad_bit2 <=    2'b0   ;
        end
        else
        begin
            cnt2       <=  cnt2_next[ 9-1:0] ;
            quad_bit2  <=  quad_bit2_next      ;
        end

    assign quad_add2      = (cnt2==9'd314 & quad_bit2==2'b00 ) |
                            (cnt2==9'd000 & quad_bit2==2'b01 ) |
                            (cnt2==9'd314 & quad_bit2==2'b10 ) |
                            (cnt2==9'd000 & quad_bit2==2'b11 )   ;

    assign quad_bit2_next = ( cntu == phase_b ) ? 2'b00  : quad_bit2 + (tau_tick&quad_add2) ;

    assign cnt2_next      = ( cntu == phase_b ) /*| ( cnt_next_zero & phase==12'b0 ) */? 10'b0   :
                            quad_add2    ? cnt2             :
                            quad_bit2[0] ? cnt2 - tau_tick  :  cnt2 + tau_tick  ;



    // ************************* *****************************************************************


    // read address engine *****************************************************************
    // for sin3f :  cnt3 , r_addr3
    reg  [ 8-1:0]  cnt3 ;
    wire [ 9-1:0]  cnt3_next ;
    reg  [ 2-1:0]  quad_bit3 ;
    wire [ 3-1:0]  quad_bit3_next ;
    wire           quad_add3;
    //wire [ 8-1:0]  r_addr3;

    always @(posedge clk)
        if (rst)
        begin
            cnt3      <=    8'b0   ;
            quad_bit3 <=    2'b0   ;
        end
        else
        begin
            cnt3       <=  cnt3_next[ 8-1:0] ;
            quad_bit3  <=  quad_bit3_next      ;
        end

    assign quad_add3      = (cnt3==8'd209 & quad_bit3==2'b00 ) |
                            (cnt3==8'd000 & quad_bit3==2'b01 ) |
                            (cnt3==8'd209 & quad_bit3==2'b10 ) |
                            (cnt3==8'd000 & quad_bit3==2'b11 )   ;

    assign quad_bit3_next = ( cntu == phase_b ) ? 2'b00  : quad_bit3 + (tau_tick&quad_add3) ;

    assign cnt3_next      = ( cntu == phase_b ) /*| ( cnt_next_zero & phase==12'b0 )*/ ? 8'b0   :
                            quad_add3    ? cnt3   :
                            quad_bit3[0] ? cnt3 - tau_tick  :  cnt3 + tau_tick  ;


    assign cos_ref  =  quad_bit[1]^quad_bit[0] ?  $signed(-memory_cos_r[cnt]) : memory_cos_r[cnt] ;
    assign sin_ref  =  quad_bit[1]             ?  $signed(-memory_sin_r[cnt]) : memory_sin_r[cnt] ;



    assign cos_1f   =  quad_bit1[1]^quad_bit1[0]   ?  $signed(-memory_cos1_r[cnt1] ) : memory_cos1_r[cnt1] ;
    assign cos_2f   =  quad_bit2[1]^quad_bit2[0]   ?  $signed(-memory_cos2_r[cnt2])  : memory_cos2_r[cnt2] ;
    assign cos_3f   =  quad_bit3[1]^quad_bit3[0]   ?  $signed(-memory_cos3_r[cnt3])  : memory_cos3_r[cnt3] ;



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
