`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company:
// Engineer:
//
// Create Date: 08.02.2017 17:17:16
// Design Name:
// Module Name: lock
// Project Name:
// Target Devices:
// Tool Versions:
// Description:
//
// Dependencies:
//
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
//
//////////////////////////////////////////////////////////////////////////////////

//(* dont_touch = "true" *)
//(* keep = "true" *)
//(* use_dsp48 = "yes" *)
//(* fsm_encoding = "gray" *)


//(* keep_hierarchy = "yes" *)
module lock(
    input clk,rst,
    // inputs
    input  signed   [14-1:0] in1,in2,
    input                    external_trigger,   // External triger input

    // outputs
    output signed   [14-1:0] out1,out2,
    output signed   [14-1:0] osc1,osc2,
    output                   trigger,            // Oscilloscope trigger output
    output                   digital_modulation, // Modulation for digital otuput
    output reg      [24-1:0] pwm_cfg_a,pwm_cfg_b,pwm_cfg_c,pwm_cfg_d,
    output reg      [32-1:0] osc_ctrl,

    // system bus
    input           [32-1:0] sys_addr        ,  //!< bus address
    input           [32-1:0] sys_wdata       ,  //!< bus write data
    input           [ 4-1:0] sys_sel         ,  //!< bus write byte select
    input                    sys_wen         ,  //!< bus write enable
    input                    sys_ren         ,  //!< bus read enable
    output reg      [32-1:0] sys_rdata       ,  //!< bus read data
    output reg               sys_err         ,  //!< bus error indicator
    output reg               sys_ack            //!< bus acknowledge signal
    );

    // Module starts here  *********************************************


    // [WIREREG DOCK]
    // gen_mod --------------------------
    reg         [12-1:0] gen_mod_phase;
    reg         [14-1:0] gen_mod_hp;
    
    // gen_ramp --------------------------
    reg                  ramp_reset,ramp_enable,ramp_direction;
    reg         [32-1:0] ramp_step;
    reg  signed [14-1:0] ramp_low_lim,ramp_hig_lim,ramp_B_factor;
    wire signed [14-1:0] ramp_A,ramp_B;
    
    // inout --------------------------
    wire signed [14-1:0] oscA,oscB;
    
    // lock-in --------------------------
    reg         [ 3-1:0] signal_sw,error_sw;
    reg         [ 4-1:0] sg_amp1,sg_amp2,sg_amp3;
    reg         [ 5-1:0] sg_amp0;
    reg         [ 6-1:0] lpf_F0,lpf_F1,lpf_F2,lpf_F3;
    reg  signed [14-1:0] error_offset,mod_out1,mod_out2;
    wire signed [14-1:0] signal_i,error;
    wire signed [32-1:0] error_mean,error_std;
    
    // lock_control --------------------------
    reg         [ 3-1:0] rl_signal_sw,rl_config;
    reg         [ 4-1:0] lock_trig_sw;
    reg         [ 5-1:0] sf_config;
    reg         [11-1:0] lock_control;
    reg         [13-1:0] rl_error_threshold;
    reg         [32-1:0] lock_trig_time;
    reg  signed [14-1:0] lock_trig_val,rl_signal_threshold,sf_jumpA,sf_jumpB;
    wire        [ 5-1:0] rl_state;
    wire        [11-1:0] lock_feedback;
    
    // mix --------------------------
    reg  signed [14-1:0] aux_A,aux_B;
    
    // modulation --------------------------
    wire signed [14-1:0] sin_ref,cos_ref,cos_1f,cos_2f,cos_3f;
    
    // outputs --------------------------
    reg         [ 4-1:0] out1_sw,out2_sw;
    
    // pidA --------------------------
    reg         [ 3-1:0] pidA_PSR,pidA_DSR,pidA_ctrl;
    reg         [ 4-1:0] pidA_ISR;
    reg         [ 5-1:0] pidA_sw;
    reg         [14-1:0] pidA_SAT;
    reg  signed [14-1:0] pidA_sp,pidA_kp,pidA_ki,pidA_kd;
    wire signed [14-1:0] pidA_in,pidA_out,ctrl_A;
    
    // pidB --------------------------
    reg         [ 3-1:0] pidB_PSR,pidB_DSR,pidB_ctrl;
    reg         [ 4-1:0] pidB_ISR;
    reg         [ 5-1:0] pidB_sw;
    reg         [14-1:0] pidB_SAT;
    reg  signed [14-1:0] pidB_sp,pidB_kp,pidB_ki,pidB_kd;
    wire signed [14-1:0] pidB_in,pidB_out,ctrl_B;
    
    // product_signals --------------------------
    reg         [ 3-1:0] read_ctrl;
    wire        [32-1:0] cnt_clk,cnt_clk2;
    wire signed [28-1:0] X_28,Y_28,F1_28,F2_28,F3_28;
    
    // scope --------------------------
    reg         [ 5-1:0] oscA_sw,oscB_sw;
    reg         [ 8-1:0] trig_sw;
    
    // [WIREREG DOCK END]

    assign rl_state = 5'b0 ; // LOLO ERASE

    wire        [14-1:0] test14;
    wire        [14-1:0] rl_signal;
    wire        [ 8-1:0] trigger_signals;

    wire        [13-1:0] error_abs ;
    wire signed [28-1:0] error_pow ;
    wire signed [41-1:0] error_mean_41;
    wire signed [54-1:0] error_std_54;

    wire                 signal_fail,error_fail,locked,out_of_lock;
    //ERASE wire                 rl_signal_threshold,rl_error_threshold;

    wire        [24-1:0] pwm_cfg_a_w,pwm_cfg_b_w,pwm_cfg_c_w,pwm_cfg_d_w;
    wire        [32-1:0] test32  ;

    //pidA_ctrl: [ pidA_ifreeze: integrator freeze , pidA_freeze: output freeze , pidA_irst:integrator reset]
    wire                 pidA_irst,pidB_irst,  pidA_freeze,pidB_freeze  , pidA_ifreeze,pidB_ifreeze;

    wire                 ramp_floor_trig,ramp_ceil_trig,harmonic_trig,param_change,lock_ctrl_trig;

    wire  signed [15-1:0] out1_plus,out2_plus;
    wire  signed [14-1:0] out1_tmp ,out2_tmp;
    //wire  signed [14-1:0] in1_lpf,in2_lpf;

    assign    pidA_irst    = pidA_ctrl[0];
    assign    pidA_freeze  = pidA_ctrl[1];
    assign    pidA_ifreeze = pidA_ctrl[2];

    assign    pidB_irst    = pidB_ctrl[0];
    assign    pidB_freeze  = pidB_ctrl[1];
    assign    pidB_ifreeze = pidB_ctrl[2];


    assign    test14 = 14'b0 ;

    wire signed  [14-1:0] error_sel , error_val ;
    wire signed  [15-1:0] error_minus_offset ;


    always @(posedge clk)
    if (rst) begin
        pwm_cfg_a  <= 24'h0 ;
        pwm_cfg_b  <= 24'h0 ;
        pwm_cfg_c  <= 24'h0 ;
        pwm_cfg_d  <= 24'h0 ;
    end
    else begin
        pwm_cfg_a  <= pwm_cfg_a_w ;
        pwm_cfg_b  <= pwm_cfg_b_w ;
        pwm_cfg_c  <= pwm_cfg_c_w ;
        pwm_cfg_d  <= pwm_cfg_d_w ;
    end

    // Definition of wires and regs ************************************

    wire                 lock_trig_rise ;
    wire                 trig_val,trig_time,set_ramp_enable,set_pidA_enable,set_pidB_enable,ramp_enable_ctrl,pidA_enable_ctrl,pidB_enable_ctrl,launch_lock_trig,lock_now;

    wire                 trigger_took_effect;

    // ERASE lolo // wire                 ramp_trig ;


    wire signed [14-1:0] Xo,Yo,F1o,F2o,F3o ;


    wire signed [14-1:0] slow_out1_14,slow_out2_14,slow_out3_14,slow_out4_14 ;
    wire        [16-1:0] slow_out1_au,slow_out2_au,slow_out3_au,slow_out4_au ;
    wire        [24-1:0] slow_out1_aux,slow_out2_aux,slow_out3_aux,slow_out4_aux ;

    wire signed [14-1:0] pidA_out_cache,pidB_out_cache ;

    wire signed [15-1:0] in1_m_in2,in1_m_in2_aux;

    wire signed [16-1:0] pidA_plus_ramp,pidB_plus_ramp;
    wire  jump_started,jump_trigger;
    wire signed [14-1:0] sf_jumpA_val,sf_jumpB_val;

    reg  signed [28-1:0] X_28_reg,Y_28_reg,F1_28_reg,F2_28_reg,F3_28_reg;
    reg  signed [14-1:0] error_reg,ctrl_A_reg,ctrl_B_reg;
    reg         [50-1:0] cnt,cnt_reg;
    wire        [50-1:0] cnt_next;
    wire                 freeze ;


    wire signed [27-1:0] out_cos1, out_cos2;

    // wires for signal processing
    //wire signed  [ 28-1: 0]   sin_ref_mult,  cos_ref_mult,   cos_1f_mult,   cos_2f_mult,   cos_3f_mult;
    wire signed  [ 28-1: 0]   cos_1f_mult,   cos_2f_mult,   cos_3f_mult;
    wire signed  [ 38-1: 0]   sin_ref_mult,  cos_ref_mult;

    //wire signed  [ 28-1: 0]   sin_ref_lpf1,  cos_ref_lpf1,   cos_1f_lpf1,   cos_2f_lpf1,   cos_3f_lpf1;
    wire signed  [ 28-1: 0]   cos_1f_lpf1,   cos_2f_lpf1,   cos_3f_lpf1;
    wire signed  [ 38-1: 0]   sin_ref_lpf1,  cos_ref_lpf1;

    //wire signed  [ 28-1: 0]   sin_ref_lpf2,  cos_ref_lpf2,   cos_1f_lpf2,   cos_2f_lpf2,   cos_3f_lpf2;
    wire signed  [ 28-1: 0]   cos_1f_lpf2,   cos_2f_lpf2,   cos_3f_lpf2;
    wire signed  [ 38-1: 0]   sin_ref_lpf2,  cos_ref_lpf2 ;

    wire signed  [  6-1: 0]       lpf_X_A,      lpf_Y_A,      lpf_F1_A,      lpf_F2_A,      lpf_F3_A;
    wire signed  [  6-1: 0]       lpf_X_B,      lpf_Y_B,      lpf_F1_B,      lpf_F2_B,      lpf_F3_B;


    //ERASE wire signed [14-1:0] LPF_A_in  , LPF_B_in  ;

    // Slow DACs decoders

    aDACdecoder i_aDACdecoder_a (  .clk(clk), .rst(rst), .in(slow_out1),  .out(pwm_cfg_a_w)  );
    aDACdecoder i_aDACdecoder_b (  .clk(clk), .rst(rst), .in(slow_out2),  .out(pwm_cfg_b_w)  );
    aDACdecoder i_aDACdecoder_c (  .clk(clk), .rst(rst), .in(slow_out3),  .out(pwm_cfg_c_w)  );
    aDACdecoder i_aDACdecoder_d (  .clk(clk), .rst(rst), .in(slow_out4),  .out(pwm_cfg_d_w)  );




    jump_control #(.N(16)) i_jump_control  ( .clk(clk), .rst(rst), .start(sf_config[0]) , .out(jump_started) , .tick(jump_trigger) );

    assign sf_jumpA_val = jump_started ? sf_jumpA : 14'b0 ;
    assign sf_jumpB_val = jump_started ? sf_jumpB : 14'b0 ;

    assign pidA_plus_ramp  = $signed(pidA_out) + $signed(ramp_A) + $signed(sf_jumpA_val) ;
    satprotect #(.Ri(16),.Ro(14),.SAT(14)) i_satprotect_ctrl_A  ( .in(pidA_plus_ramp),  .out(ctrl_A) );

    assign pidB_plus_ramp = $signed(pidB_out) + $signed(ramp_B)  + $signed(sf_jumpB_val) ;
    satprotect #(.Ri(16),.Ro(14),.SAT(14)) i_satprotect_ctrl_B  ( .in(pidB_plus_ramp),  .out(ctrl_B) );

    // Muxers  *********************************************************

    // Scopes outputs *************
    muxer_reg5  #(.RES(14)) i_muxer5_scope1 (
        // input
        .clk(clk), .rst(rst),
        .sel  ( oscA_sw ), // select cable
        .in0  ( 14'b0 ),
        .in1  ( in1     ),   .in2  ( in2     ),
        .in3  ( error  ),
        .in4  ( ctrl_A  ),   .in5  ( ctrl_B  ),
        .in6  ( ramp_A  ),   .in7  ( ramp_B  ),
        .in8  ( pidA_in ),   .in9  ( pidB_in ),
        .in10 ( pidA_out_cache ),    .in11 ( pidB_out_cache  ),
        .in12 ( sin_ref ),   .in13 ( cos_ref ),
        .in14 ( cos_1f ),    .in15 ( cos_2f  ),   .in16 ( cos_3f  ),
        .in17 ( Xo  )   ,    .in18 ( Yo      ),
        .in19 ( F1o )   ,    .in20 ( F2o     ),   .in21 ( F3o     ),
        .in22 ( signal_i ),
        .in23 ( out1     ),  .in24 ( out2    ),
        .in25 (  14'b0    ),  .in26 (  14'b0    ),
        .in27 ( 14'b0   ),   .in28 ( 14'b0 ), .in29 (  14'b0 ),
        .in30 ( 14'b0 ), // in30
        .in31 ( 14'b0 ), // in31
        // output
        .out ( oscA  )
    );

    muxer_reg5  #(.RES(14)) i_muxer5_scope2 (
        // input
        .clk(clk), .rst(rst),
        .sel  ( oscB_sw ), // select cable
        .in0  ( 14'b0 ),
        .in1  ( in1     ),   .in2  ( in2     ),
        .in3  ( error  ),
        .in4  ( ctrl_A  ),   .in5  ( ctrl_B  ),
        .in6  ( ramp_A  ),   .in7  ( ramp_B  ),
        .in8  ( pidA_in ),   .in9  ( pidB_in ),
        .in10 ( pidA_out_cache ),    .in11 ( pidB_out_cache  ),
        .in12 ( sin_ref ),   .in13 ( cos_ref ),
        .in14 ( cos_1f ),    .in15 ( cos_2f  ),   .in16 ( cos_3f  ),
        .in17 ( Xo  )   ,    .in18 ( Yo      ),
        .in19 ( F1o )   ,    .in20 ( F2o     ),   .in21 ( F3o     ),
        .in22 ( signal_i ),
        .in23 ( out1     ),  .in24 ( out2    ),
        .in25 (  14'b0    ),  .in26 (  14'b0    ),
        .in27 ( 14'b0   ),   .in28 ( 14'b0 ), .in29 (  14'b0 ),
        .in30 ( 14'b0 ), // in30
        .in31 ( 14'b0 ), // in31
        // output
        .out ( oscB  )
    );

    assign osc1 = oscA;
    assign osc2 = oscB;


    //  External Trigger  selection ******************

    //assign trigger          = trig_time ? ramp_trig : external_trigger ;
    // items=['Pin','Ramp floor','Ramp ceil','harmonic mod.','Square mod.','Out of lock','Param. change'],

    assign  param_change    = 1'b0; // LOLO complete

    assign  trigger_signals = {  lock_ctrl_trig   ,
                                 jump_trigger     ,
                                 out_of_lock      ,
                                 1'b0 ,    //square_trig      ,
                                 harmonic_trig    ,
                                 ramp_ceil_trig   ,
                                 ramp_floor_trig  ,
                                 external_trigger
                              } ;


    //assign trigger          = trigger_signals & trig_sw ;

    trigger_input  #(.R(8),.N(3)) i_trigger_input (
        // input
        .clk(clk), .rst(rst),
        .trig_in ( trigger_signals ),
        .trig_sel( trig_sw         ),
        // output
        .trig_tick(trigger)
    ) ;


    // Fast DAC outputs *************

    muxer4  #(.RES(14)) out1_sw_m (
        // input
        .sel  ( out1_sw           ), // select cable
        .in0  ( 14'b0             ), // in0
        .in1  ( in1               ), // in1
        .in2  ( in2               ), // in1-in2
        .in3  ( in1_m_in2[14-1:0] ), // in3
        .in4  ( error           ), // in4
        .in5  ( cos_1f            ), // in5
        .in6  ( cos_2f            ), // in6
        .in7  ( cos_3f            ), // in7
        .in8  ( cos_ref           ), // in8
        .in9  ( sin_ref           ), // in9
        .in10 ( pidA_out           ), // in10
        .in11 ( pidB_out          ), // in11
        .in12 ( ctrl_A            ), // in12
        .in13 ( ctrl_B            ), // in13
        .in14 ( aux_A             ), // in14
        .in15 ( aux_B             ), // in15

        // output
        .out ( out1_tmp   )
    );


    muxer4  #(.RES(14)) out2_sw_m (
        // input
        .sel  ( out2_sw          ), // select cable
        .in0  ( 14'b0             ), // in0
        .in1  ( in1               ), // in1
        .in2  ( in2               ), // in1-in2
        .in3  ( in1_m_in2[14-1:0] ), // in3
        .in4  ( error           ), // in4
        .in5  ( cos_1f            ), // in5
        .in6  ( cos_2f            ), // in6
        .in7  ( cos_3f            ), // in7
        .in8  ( cos_ref           ), // in8
        .in9  ( sin_ref           ), // in9
        .in10 ( pidA_out           ), // in10
        .in11 ( pidB_out          ), // in11
        .in12 ( ctrl_A            ), // in12
        .in13 ( ctrl_B            ), // in13
        .in14 ( aux_A             ), // in14
        .in15 ( aux_B             ), // in15
        // output
        .out ( out2_tmp  )
    );


    // Adding modulation to outputs

    assign out_cos1    = ($signed(mod_out1) * $signed(cos_ref)) >>> 13 ;
    assign out_cos2    = ($signed(mod_out2) * $signed(sin_ref)) >>> 13 ;

    assign out1_plus   = ~mod_out1[13] ? $signed(out1_tmp) + $signed(out_cos1[14-1:0]) : $signed(out1_tmp) ;
    assign out2_plus   = ~mod_out2[13] ? $signed(out2_tmp) + $signed(out_cos2[14-1:0]) : $signed(out2_tmp) ;

    satprotect #(.Ri(15),.Ro(14),.SAT(14)) i_satprotect_out1  ( .in(out1_plus),  .out(out1) );
    satprotect #(.Ri(15),.Ro(14),.SAT(14)) i_satprotect_out2  ( .in(out2_plus),  .out(out2) );


    // test an debug



    // Slow DACs outputs *************
    // map to 0 - 1.8 V

    //assign slow_out1_au  =  $signed(slow_out1_14) + $signed(15'd8192)  ;
    //assign slow_out2_au  =  $signed(slow_out2_14) + $signed(15'd8192)  ;
    assign slow_out3_au  =  $signed(slow_out3_14) + $signed(15'd8192)  ;
    assign slow_out4_au  =  $signed(slow_out4_14) + $signed(15'd8192)  ;

    //assign slow_out1_aux = slow_out1_au * 8'd156 ;
    //assign slow_out2_aux = slow_out2_au * 8'd156 ;

    pipe_mult #(.R(16),.level(4)) i_mult_slow_out3_aux (.clk(clk), .a(slow_out3_au) , .b(16'd156), .pdt(slow_out3_aux));
    pipe_mult #(.R(16),.level(4)) i_mult_slow_out4_aux (.clk(clk), .a(slow_out4_au) , .b(16'd156), .pdt(slow_out4_aux));
    //assign slow_out3_aux = slow_out3_au * 8'd156 ;
    //assign slow_out4_aux = slow_out4_au * 8'd156 ;

    //assign slow_out1     = slow_out1_aux[22-1:10];
    //assign slow_out2     = slow_out2_aux[22-1:10];
    assign slow_out3     = slow_out3_aux[22-1:10];
    assign slow_out4     = slow_out4_aux[22-1:10];





    assign     slow_out1_14 = 14'b10000000000000 ;
    assign     slow_out2_14 = 14'b10000000000000 ;


    muxer_reg4  #(.RES(14)) slow_out3_sw_m (
        // input
        .clk(clk), .rst(rst),
        .sel  ( slow_out3_sw ), // select cable
        .in0  ( 14'b10000000000000),
        .in1  ( in1               ), // in1
        .in2  ( in2               ), // in1-in2
        .in3  ( in1_m_in2[14-1:0] ), // in3
        .in4  ( sin_ref           ), // in4
        .in5  ( cos_1f            ), // in5
        .in6  ( cos_2f            ), // in6
        .in7  ( cos_3f            ), // in7
        .in8  ( /*sq_ref*/ 14'b0            ), // in8
        .in9  ( /*sq_phas*/ 14'b0           ), // in9
        .in10 ( ramp_A            ), // in10
        .in11 ( pidA_out          ), // in11
        .in12 ( ctrl_A            ), // in12
        .in13 ( ctrl_B            ), // in13
        .in14 ( error             ), // in14
        .in15 ( aux_A             ), // in15
        // output
        .out ( slow_out3_14  )
    );


    muxer_reg4  #(.RES(14)) slow_out4_sw_m (
        // input
        .clk(clk), .rst(rst),
        .sel  ( slow_out4_sw ), // select cable
        .in0  ( 14'b10000000000000),
        .in1  ( in1               ), // in1
        .in2  ( in2               ), // in1-in2
        .in3  ( in1_m_in2[14-1:0] ), // in3
        .in4  ( cos_ref           ), // in4
        .in5  ( cos_1f            ), // in5
        .in6  ( cos_2f            ), // in6
        .in7  ( cos_3f            ), // in7
        .in8  ( /*sq_quad*/ 14'b0           ), // in8
        .in9  ( /*sq_phas*/ 14'b0           ), // in9
        .in10 ( ramp_B            ), // in10
        .in11 ( pidA_out          ), // in11
        .in12 ( ctrl_A            ), // in12
        .in13 ( ctrl_B            ), // in13
        .in14 ( error             ), // in14
        .in15 ( aux_B             ), // in15
        // output
        .out ( slow_out4_14  )
    );

    // signal_i conditioning  ******************************************

    assign in1_m_in2_aux = $signed(in1) - $signed(in2) ;
    sat14 #(.RES(15)) i_sat15_in1in2 ( .in(in1_m_in2_aux), .lim( 15'd13  ), .out(in1_m_in2) );

    muxer3  #(.RES(14)) muxer_signal_i (
        // input
        .sel (  signal_sw  ), // select cable
        .in0  ( in1 ), // in0
        .in1  ( in2 ), // in1
        .in2  ( in1_m_in2[14-1:0] ), // in1-in2
        .in3  ( cos_ref ), // in3
        .in4  ( sin_ref ), // in4
        .in5  ( cos_1f ), // in5
        .in6  ( aux_A ), // in6
        .in7  ( ramp_A ), // in7
        // output
        .out ( signal_i   )
    );


    muxer_reg3  #(.RES(14)) muxer3_error_i (
        // input
        .clk(clk), .rst(rst),
        .sel  (  error_sw  ), // select cable
        .in0  ( 14'b0      ), // in11
        .in1  ( Xo         ), // in0
        .in2  ( Yo         ), // in3
        .in3  ( F1o        ), // in5
        .in4  ( F2o        ), // in7
        .in5  ( F3o        ), // in8
        .in6  ( in1        ), // in9
        .in7  ( in1_m_in2[14-1:0]    ), // in10
        // output
        .out ( error_sel   )
    );


    assign error_minus_offset  = $signed(error_sel) - $signed(error_offset);
    //satprotect #(.Ri(15),.Ro(14),.SAT(14)) i_satprotect_error  ( .in(error_minus_offset),  .out(error) );

    assign error = $signed(error_minus_offset[14-1:0]) ;

    sum_2N2  #(.R1(27),.R2(14),.N(27)) i_sum_2N_error_std  (.clk(clk), .rst(rst), .in1( error_pow[27-1:0] ), .out1( error_std_54  ) , .in2( error     ), .out2( error_mean_41 ));

    assign error_mean = $signed( error_mean_41[41-1:9] );
    assign error_std  = $signed( error_std_54[54-1:22] ) ;
    //assign error_pow  = $signed(error) * $signed(error);

    // mult_dsp_14  i_mult_dps_error_pow (.CLK(clk), .A($signed(error)) , .B(error), .P(error_pow));
    pipe_mult #(.R(13),.level(4)) i_mult_error_pow (.clk(clk), .a(error_abs) , .b(error_abs), .pdt(error_pow));


    // Function generator **********************************************

    gen_mod_h  i_gen_mod (
       // input
      .clk       (  clk              ),  // clock
      .rst       (  rst              ),  // reset - active low
      .phase     (  gen_mod_phase    ),  // phase
      .hp        (  gen_mod_hp       ),  // harmonic period

      // output
      .cntu_w    (               ),  // LOLO ERASE
      .sin_ref   (  sin_ref      ),  // sinus
      .cos_1f    (  cos_1f       ),  // sinus with phase
      .cos_2f    (  cos_2f       ),  // sinus with phase and 2f
      .cos_3f    (  cos_3f       ),  // sinus with phase and 3f
      .cos_ref   (  cos_ref      ),  // cosinus
      .harmonic_trig ( harmonic_trig )//, // harmonic trigger

    );

    assign digital_modulation = 1'b0 ;

    /* end function generator *****************************************/


    // Ramp generator **************************************************

    gen_ramp #(.R(14)) i_gen_ramp (
        .clk(clk),  .rst(rst),
        // inputs
        .ramp_step     ( ramp_step       ),
        .ramp_low_lim  ( ramp_low_lim    ),
        .ramp_hig_lim  ( ramp_hig_lim    ),
        .ramp_reset    ( ramp_reset      ),
        .ramp_enable   ( ramp_enable & ramp_enable_ctrl    ),
        .ramp_direction( ramp_direction  ),
        .ramp_B_factor ( ramp_B_factor   ),
        .relock_enable ( |rl_config[1:0] ),
        .out_of_lock   ( out_of_lock     ),
        .relock_reset  ( rl_config[2]    ),
        // outputs
        .trigger_low   ( ramp_floor_trig ),
        .trigger_hig   ( ramp_ceil_trig  ),
        .outA          ( ramp_A          ),
        .outB          ( ramp_B          )
    );


    /* end Ramp generator *********************************************/


    // LOCK control  ***************************************************

    wire signed [ 14-1:0] lock_ctrl_signal;

    muxer4  #(.RES(14)) i_muxer4_lock_trig_sw (
        // input
        .sel  ( lock_trig_sw ), // select cable
        .in0  ( error             ), // in0
        .in1  ( Xo                ), // in1
        .in2  ( Yo                ), // in1-in2
        .in3  ( F1o               ), // in3
        .in4  ( F2o               ), // in4
        .in5  ( F3o               ), // in5
        .in6  ( /*sqXo */ 14'b0             ), // in6
        .in7  ( /*sqYo */ 14'b0             ), // in7
        .in8  ( /*sqFo */ 14'b0             ), // in8
        .in9  ( signal_i          ), // in9
        .in10 ( ramp_A            ), // in10
        .in11 ( aux_A             ), // in11
        .in12 ( in1               ), // in12
        .in13 ( in2               ), // in13
        .in14 ( in1_m_in2[14-1:0] ), // in14
        .in15 ( pidA_out_cache    ), // in15
        // output
        .out ( lock_ctrl_signal  )
    );

    wire trigger_found_aux;

    lock_ctrl i_lock_ctrl (
        .clk(clk),  .rst(rst),
        // inputs
        .lock_ctrl            ( lock_control[9:0]  ),
        .signal               ( lock_ctrl_signal   ),
        .ramp_trigger         ( ramp_floor_trig    ),
        .time_threshold       ( lock_trig_time     ),
        .level_threshold      ( lock_trig_val      ),
        .level_rising_trigger ( lock_trig_rise     ),
        // outputs
        .ramp_enable          ( ramp_enable_ctrl   ),
        .pidA_enable          ( pidA_enable_ctrl   ),
        .pidB_enable          ( pidB_enable_ctrl   ),
        .lock_ctrl_trig       ( lock_ctrl_trig     )
    );

    assign lock_trig_rise      =  lock_control[10];
    assign trigger_took_effect = &{ ~(ramp_enable_ctrl^lock_control[7]) , ~(pidA_enable_ctrl^lock_control[6]) , ~(pidB_enable_ctrl^lock_control[5]) } ;

    wire  [2-1:0]  next_lock_cmd;
    assign next_lock_cmd       = trigger_took_effect ? 2'b0 : lock_control[1:0] ;
    assign lock_feedback =   { lock_control[10:5]  ,
                               ramp_enable_ctrl ,
                               pidA_enable_ctrl ,
                               pidB_enable_ctrl ,
                               next_lock_cmd
                               };

    assign   trig_time        =   lock_control[8];


    muxer3  #(.RES(14)) muxer3_rl_signal_sw (
        // input
        .sel (  rl_signal_sw  ), // select cable
        .in0  ( in1   ), // in0
        .in1  ( in2   ), // in1
        .in2  ( in1_m_in2[14-1:0] ), // in2
        .in3  ( aux_A ), // in3
        .in4  ( aux_B ), // in4
        .in5  ( 14'b0 ), // in5 LOLO F1 F2 F3
        .in6  ( 14'b0 ), // in6
        .in7  ( 14'b0 ), // in7
        // output
        .out ( rl_signal   )
    );


    assign rl_signal_enable = rl_config[1] ;
    assign rl_error_enable  = rl_config[0] ;

    assign error_abs = error[13] ? (~error[13-1:0]) + 1'b1  : error[13-1:0] ;

    assign signal_fail = /*enable_signal_th ?*/ rl_signal < rl_signal_threshold /*: 1'b0*/ ;
    assign error_fail  = /*enable_error_th  ?*/ error_abs >  rl_error_threshold /*: 1'b0 */;
    //assign out_of_lock = (|rl_config[1:0]) ? signal_fail|error_fail : 1'b0 ;

    debounce #(.N0(7),.N1(4)) i_debounce_out_of_lock ( .clk(clk), .reset(rst), .in(signal_fail|error_fail), .db_level(out_of_lock), .db_tick ( )  );


    /* end LOCK control  **********************************************/



    // Signal Processing  **********************************************

    assign     lpf_X_A   =   { ~lpf_F0[5], ~lpf_F0[5], lpf_F0[4-1:0]} ;
    assign     lpf_Y_A   =   { ~lpf_F0[5], ~lpf_F0[5], lpf_F0[4-1:0]} ;
    assign     lpf_F1_A   =   { ~lpf_F1[5], ~lpf_F1[5], lpf_F1[4-1:0]} ;
    assign     lpf_F2_A   =   { ~lpf_F2[5], ~lpf_F2[5], lpf_F2[4-1:0]} ;
    assign     lpf_F3_A   =   { ~lpf_F3[5], ~lpf_F3[5], lpf_F3[4-1:0]} ;


    assign     lpf_X_B   =   { ~(^lpf_F0[5:4]), ~(^lpf_F0[5:4]), lpf_F0[4-1:0]} ;
    assign     lpf_Y_B   =   { ~(^lpf_F0[5:4]), ~(^lpf_F0[5:4]), lpf_F0[4-1:0]} ;
    assign     lpf_F1_B   =   { ~(^lpf_F1[5:4]), ~(^lpf_F1[5:4]), lpf_F1[4-1:0]} ;
    assign     lpf_F2_B   =   { ~(^lpf_F2[5:4]), ~(^lpf_F2[5:4]), lpf_F2[4-1:0]} ;
    assign     lpf_F3_B   =   { ~(^lpf_F3[5:4]), ~(^lpf_F3[5:4]), lpf_F3[4-1:0]} ;




    // signal_i multiplied by reference signal

    wire signed [28-1:0] sin_ref_mult_tmp_28, cos_ref_mult_tmp_28; // this is for amplitud enhancement

    mult_dsp_14  i_mult_dps_sin_ref (.CLK(clk), .A($signed(sin_ref)) , .B(signal_i), .P(sin_ref_mult_tmp_28));
    mult_dsp_14  i_mult_dps_cos_ref (.CLK(clk), .A($signed(cos_ref)) , .B(signal_i), .P(cos_ref_mult_tmp_28));
    mult_dsp_14  i_mult_dps_cos_1f  (.CLK(clk), .A($signed(cos_1f )) , .B(signal_i), .P(cos_1f_mult ));
    mult_dsp_14  i_mult_dps_cos_2f  (.CLK(clk), .A($signed(cos_2f )) , .B(signal_i), .P(cos_2f_mult ));
    mult_dsp_14  i_mult_dps_cos_3f  (.CLK(clk), .A($signed(cos_3f )) , .B(signal_i), .P(cos_3f_mult ));

    assign sin_ref_mult = sin_ref_mult_tmp_28 <<< 4'd10 ; // this is for amplitud enhancement
    assign cos_ref_mult = cos_ref_mult_tmp_28 <<< 4'd10 ;

    // multiplied signal " "_mult goes in LPF_?_A
    LP_filter3 #(.R(38)) i_LP_filter_sin_ref_A (.clk(clk), .rst(rst), .tau( lpf_X_A   ), .in( sin_ref_mult ), .out( sin_ref_lpf1 ) );
    LP_filter3 #(.R(38)) i_LP_filter_cos_ref_A (.clk(clk), .rst(rst), .tau( lpf_Y_A   ), .in( cos_ref_mult ), .out( cos_ref_lpf1 ) );
    LP_filter3 #(.R(28)) i_LP_filter_cos_1f_A  (.clk(clk), .rst(rst), .tau( lpf_F1_A  ), .in( cos_1f_mult  ), .out( cos_1f_lpf1  ) );
    LP_filter3 #(.R(28)) i_LP_filter_cos_2f_A  (.clk(clk), .rst(rst), .tau( lpf_F2_A  ), .in( cos_2f_mult  ), .out( cos_2f_lpf1  ) );
    LP_filter3 #(.R(28)) i_LP_filter_cos_3f_A  (.clk(clk), .rst(rst), .tau( lpf_F3_A  ), .in( cos_3f_mult  ), .out( cos_3f_lpf1  ) );


    // LPF_A goes into LPF_?_B
    LP_filter3 #(.R(38)) i_LP_filter_sin_ref_B (.clk(clk), .rst(rst), .tau( lpf_X_B   ), .in( sin_ref_lpf1 ), .out( sin_ref_lpf2 ) );
    LP_filter3 #(.R(38)) i_LP_filter_cos_ref_B (.clk(clk), .rst(rst), .tau( lpf_Y_B   ), .in( cos_ref_lpf1 ), .out( cos_ref_lpf2 ) );
    LP_filter3 #(.R(28)) i_LP_filter_cos_1f_B  (.clk(clk), .rst(rst), .tau( lpf_F1_B  ), .in( cos_1f_lpf1  ), .out( cos_1f_lpf2  ) );
    LP_filter3 #(.R(28)) i_LP_filter_cos_2f_B  (.clk(clk), .rst(rst), .tau( lpf_F2_B  ), .in( cos_2f_lpf1  ), .out( cos_2f_lpf2  ) );
    LP_filter3 #(.R(28)) i_LP_filter_cos_3f_B  (.clk(clk), .rst(rst), .tau( lpf_F3_B  ), .in( cos_3f_lpf1  ), .out( cos_3f_lpf2  ) );


    //wire signed [37-1:0] Xo_37,Yo_37,F1o_37,F2o_37,F3o_37;
    wire signed [47-1:0] Xo_47,Yo_47;
    wire signed [37-1:0] F1o_37,F2o_37,F3o_37;

    //wire signed [28-1:0] Xo_28,Yo_28,F1o_28,F2o_28,F3o_28;
    wire signed [38-1:0] Xo_38,Yo_38;
    wire signed [28-1:0] F1o_28,F2o_28,F3o_28;

    assign X_28   = cos_ref_lpf2 >>> 4'd10 ;
    assign Y_28   = sin_ref_lpf2 >>> 4'd10 ;
    assign F1_28  = cos_1f_lpf2  ;
    assign F2_28  = cos_2f_lpf2  ;
    assign F3_28  = cos_3f_lpf2  ;



    assign Xo_47    = ( cos_ref_lpf2   <<< sg_amp0  );
    assign Yo_47    = ( sin_ref_lpf2   <<< sg_amp0  );
    assign F1o_37   = ( F1_28  <<< sg_amp1  );
    assign F2o_37   = ( F2_28  <<< sg_amp2  );
    assign F3o_37   = ( F3_28  <<< sg_amp3  );




    satprotect #(.Ri(47),.Ro(38),.SAT(38)) i_satprotect_Xo_47   ( .in( Xo_47  ), .out( Xo_38  ) );
    satprotect #(.Ri(47),.Ro(38),.SAT(38)) i_satprotect_Yo_47   ( .in( Yo_47  ), .out( Yo_38  ) );
    satprotect #(.Ri(37),.Ro(28),.SAT(28)) i_satprotect_F1o_37  ( .in( F1o_37 ), .out( F1o_28 ) );
    satprotect #(.Ri(37),.Ro(28),.SAT(28)) i_satprotect_F2o_37  ( .in( F2o_37 ), .out( F2o_28 ) );
    satprotect #(.Ri(37),.Ro(28),.SAT(28)) i_satprotect_F3o_37  ( .in( F3o_37 ), .out( F3o_28 ) );





    always @(posedge clk) begin
        if(rst) begin
            X_28_reg   <=  28'b0;
            Y_28_reg   <=  28'b0;
            F1_28_reg   <=  28'b0;
            F2_28_reg   <=  28'b0;
            F3_28_reg   <=  28'b0;

            error_reg   <=  14'b0;
            ctrl_A_reg  <=  14'b0;
            ctrl_B_reg  <=  14'b0;
            cnt         <=  50'b0;
            cnt_reg     <=  50'b0;
        end
        else begin
            if(freeze) begin
                X_28_reg    <=  X_28_reg;
                Y_28_reg    <=  Y_28_reg;
                F1_28_reg   <=  F1_28_reg;
                F2_28_reg   <=  F2_28_reg;
                F3_28_reg   <=  F3_28_reg;

                error_reg   <=  error_reg;
                ctrl_A_reg  <=  ctrl_A_reg;
                ctrl_B_reg  <=  ctrl_B_reg;
                cnt_reg     <=  cnt_reg;
            end
            else begin
                X_28_reg    <=  X_28;
                Y_28_reg    <=  Y_28;
                F1_28_reg   <=  F1_28;
                F2_28_reg   <=  F2_28;
                F3_28_reg   <=  F3_28;
                error_reg   <=  error;
                ctrl_A_reg  <=  ctrl_A;
                ctrl_B_reg  <=  ctrl_B;
                cnt_reg     <=  cnt;
            end
            cnt     <=  cnt_next;
        end
    end

    assign freeze   = read_ctrl[0] ;
    assign cnt_clk  = cnt_reg[32-1:0] ;
    assign cnt_clk2 = { 14'b0, cnt_reg[50-1:32] } ;
    assign cnt_next = read_ctrl[1] ? cnt + 1'b1 : 50'b0 ;
    //read_ctrl

    // Amplified signal output

    wire signed [16-1:0] Xo_16,Yo_16,F1o_16,F2o_16,F3o_16;


    assign Xo_16   = $signed(Xo_38[  37-1:21]) + Xo_38[  20] ;
    assign Yo_16   = $signed(Yo_38[  37-1:21]) + Yo_38[  20] ;
    assign F1o_16  = $signed(F1o_28[ 27-1:11]) + F1o_28[ 10] ;
    assign F2o_16  = $signed(F2o_28[ 27-1:11]) + F2o_28[ 10] ;
    assign F3o_16  = $signed(F3o_28[ 27-1:11]) + F3o_28[ 10] ;


    satprotect #(.Ri(16),.Ro(14),.SAT(14)) i_satprotect_Xo    ( .in( Xo_16 ),     .out( Xo    ) );
    satprotect #(.Ri(16),.Ro(14),.SAT(14)) i_satprotect_Yo    ( .in( Yo_16 ),     .out( Yo    ) );
    satprotect #(.Ri(16),.Ro(14),.SAT(14)) i_satprotect_F1o   ( .in( F1o_16 ),    .out( F1o   ) );
    satprotect #(.Ri(16),.Ro(14),.SAT(14)) i_satprotect_F2o   ( .in( F2o_16 ),    .out( F2o   ) );
    satprotect #(.Ri(16),.Ro(14),.SAT(14)) i_satprotect_F3o   ( .in( F3o_16 ),    .out( F3o   ) );

    /* end Signal Processing  *****************************************/



    // PIDs Blocks  ****************************************************

    muxer4  #(.RES(14)) i_muxer5_pidA (
        // input
        .sel  ( pidA_sw ), // select cable
        .in0   ( error          ),
        .in1   ( Xo             ),        .in2   ( Yo             ),
        .in3   ( F1o            ),        .in4   ( F2o            ),        .in5   ( F3o            ),
        .in6   ( signal_i       ),        .in7   ( ramp_A         ),
        .in8   ( in1_m_in2[14-1:0] ),     .in9   ( in1            ),        .in10  (  in2           ),
        .in11  ( aux_A          ),        .in12  ( aux_B          ),
        .in13  ( cos_ref         ),       .in14  ( sin_ref        ),
        .in15  ( 14'b0         ),
        // output
        .out ( pidA_in  )
    );

    wire   pidA_freeze_sf,pidA_ifreeze_sf;
    assign pidA_freeze_sf  = sf_config[1] & jump_started ;
    assign pidA_ifreeze_sf = sf_config[2] & jump_started ;

    lock_pid_block i_lock_pid_block_A (
       // data
      .clk_i        (  clk            ),  // clock
      .rstn_i       (  rst            ),  // reset
      .pid_freeze   (  pidA_freeze  | pidA_freeze_sf   ),  // freeze output value
      .pid_ifreeze  (  pidA_ifreeze | pidA_ifreeze_sf  ),  // freeze integrator memory value
      .dat_i        (  pidA_in        ),  // input data
      .sat_i        (  pidA_SAT       ),  // saturacion
      .dat_o        (  pidA_out_cache ),  // output data

       // settings

      .PSR          (  pidA_PSR     ),
      .ISR          (  pidA_ISR     ),
      .DSR          (  pidA_DSR     ),

      .set_sp_i     (  pidA_sp      ),  // set point
      .set_kp_i     (  pidA_kp      ),  // Kp
      .set_ki_i     (  pidA_ki      ),  // Ki
      .set_kd_i     (  pidA_kd      ),  // Kd
      .int_rst_i    (  pidA_irst|(~pidA_enable_ctrl)    )   // integrator reset
    );

    assign pidA_out = pidA_enable_ctrl ? pidA_out_cache : 14'b0 ;

    muxer4  #(.RES(14)) i_muxer5_pidB (
        // input
        .sel  ( pidB_sw ), // select cable
        .in0   ( error          ),
        .in1   ( Xo             ),        .in2   ( Yo             ),
        .in3   ( F1o            ),        .in4   ( F2o            ),        .in5   ( F3o            ),
        .in6   ( signal_i       ),        .in7   ( ramp_A         ),
        .in8   ( in1_m_in2[14-1:0] ),     .in9   ( in1            ),        .in10  (  in2           ),
        .in11  ( aux_A          ),        .in12  ( aux_B          ),
        .in13  ( cos_ref         ),       .in14  ( sin_ref        ),
        .in15  ( 14'b0         ),
        // output
        .out ( pidB_in  )
    );

    wire   pidB_freeze_sf,pidB_ifreeze_sf;
    assign pidB_freeze_sf  = sf_config[3] & jump_started ;
    assign pidB_ifreeze_sf = sf_config[4] & jump_started ;

    lock_pid_block i_lock_pid_block_B (
       // data
      .clk_i        (  clk            ),  // clock
      .rstn_i       (  rst            ),  // reset
      .pid_freeze   (  pidB_freeze   | pidB_freeze_sf  ),  // freeze output value
      .pid_ifreeze  (  pidB_ifreeze  | pidB_ifreeze_sf ),  // freeze integrator memory value
      .dat_i        (  pidB_in        ),  // input data
      .sat_i        (  pidB_SAT       ),  // saturacion
      .dat_o        (  pidB_out_cache       ),  // output data

       // settings

      .PSR          (  pidB_PSR     ),
      .ISR          (  pidB_ISR     ),
      .DSR          (  pidB_DSR     ),

      .set_sp_i     (  pidB_sp      ),  // set point
      .set_kp_i     (  pidB_kp      ),  // Kp
      .set_ki_i     (  pidB_ki      ),  // Ki
      .set_kd_i     (  pidB_kd      ),  // Kd
      .int_rst_i    (  pidB_irst|(~pidB_enable_ctrl)    )   // integrator reset
    );

    assign pidB_out = pidB_enable_ctrl ? pidB_out_cache : 14'b0 ;


    /* end PIDs Blocks  ***********************************************/



    // [FPGA MEMORY DOCK]
    //---------------------------------------------------------------------------------
    //
    //  System bus connection
    
    // SO --> MEMORIA --> FPGA
    
    always @(posedge clk)
    if (rst) begin
        oscA_sw                <=   5'd1     ; // switch for muxer oscA
        oscB_sw                <=   5'd2     ; // switch for muxer oscB
        osc_ctrl               <=   2'd3     ; // oscilloscope control // [osc2_filt_off,osc1_filt_off]
        trig_sw                <=   8'd0     ; // Select the external trigger signal
        out1_sw                <=   4'd0     ; // switch for muxer out1
        out2_sw                <=   4'd0     ; // switch for muxer out2
        lock_control           <=  11'd1148  ; // lock_control help
        lock_trig_val          <=  14'd0     ; // if lock_control ?? , this vals sets the voltage threshold that turns on the lock
        lock_trig_time         <=  32'd0     ; // if lock_control ?? , this vals sets the time threshold that turns on the lock
        lock_trig_sw           <=   4'd0     ; // selects signal for trigger
        rl_error_threshold     <=  13'd0     ; // Threshold for error signal. Launchs relock when |error| > rl_error_threshold
        rl_signal_sw           <=   3'd0     ; // selects signal for relock trigger
        rl_signal_threshold    <=  14'd0     ; // Threshold for signal. Launchs relock when signal < rl_signal_threshold
        rl_config              <=   3'd0     ; // Relock enable. [relock_reset,enable_signal_th,enable_error_th] 
        sf_jumpA               <=  14'd0     ; // Step function measure jump value for ctrl_A
        sf_jumpB               <=  14'd0     ; // Step function measure jump value for ctrl_B
        sf_config              <=   5'd0     ; // Step function configuration. [pidB_ifreeze,pidB_freeze,pidA_ifreeze,pidA_freeze,start] 
        signal_sw              <=   3'd0     ; // Input selector for signal_i
        sg_amp0                <=   5'd0     ; // amplification of Xo, Yo
        sg_amp1                <=   4'd0     ; // amplification F1o
        sg_amp2                <=   4'd0     ; // amplification of F2o
        sg_amp3                <=   4'd0     ; // amplification of F3o
        lpf_F0                 <=   6'd32    ; // Low Pass Filter of X, Y
        lpf_F1                 <=   6'd32    ; // Low Pass Filter F1
        lpf_F2                 <=   6'd32    ; // Low Pass Filter of F2
        lpf_F3                 <=   6'd32    ; // Low Pass Filter of F3
        error_sw               <=   3'd0     ; // select error signal
        error_offset           <=  14'd0     ; // offset for the error signal
        mod_out1               <= -14'd1     ; // Modulation amplitud for out1
        mod_out2               <= -14'd1     ; // Modulation amplitud for out2
        gen_mod_phase          <=  12'd0     ; // phase relation of cos_?f signals
        gen_mod_hp             <=  14'd0     ; // harmonic period set
        ramp_step              <=  32'd0     ; // period of the triangular ramp signal
        ramp_low_lim           <= -14'd5000  ; // ramp low limit
        ramp_hig_lim           <=  14'd5000  ; // ramp high limit
        ramp_reset             <=   1'd0     ; // ramp reset config
        ramp_enable            <=   1'd0     ; // ramp enable/disable switch
        ramp_direction         <=   1'd0     ; // ramp starting direction (up/down)
        ramp_B_factor          <=  14'd4096  ; // proportional factor ramp_A/ramp_B. // ramp_B=ramp_A*ramp_B_factor/4096
        read_ctrl              <=   3'd0     ; // [unused,start_clk,Freeze]
        pidA_sw                <=   5'd0     ; // switch selector for pidA input
        pidA_PSR               <=   3'd3     ; // pidA PSR
        pidA_ISR               <=   4'd8     ; // pidA ISR
        pidA_DSR               <=   3'd0     ; // pidA DSR
        pidA_SAT               <=  14'd13    ; // pidA saturation control
        pidA_sp                <=  14'd0     ; // pidA set_point
        pidA_kp                <=  14'd0     ; // pidA proportional constant
        pidA_ki                <=  14'd0     ; // pidA integral constant
        pidA_kd                <=  14'd0     ; // pidA derivative constant
        pidA_ctrl              <=   3'd0     ; // pidA control: [ pidA_ifreeze: integrator freeze , pidA_freeze: output freeze , pidA_irst:integrator reset]
        pidB_sw                <=   5'd0     ; // switch selector for pidB input
        pidB_PSR               <=   3'd3     ; // pidB PSR
        pidB_ISR               <=   4'd8     ; // pidB ISR
        pidB_DSR               <=   3'd0     ; // pidB DSR
        pidB_SAT               <=  14'd13    ; // pidB saturation control
        pidB_sp                <=  14'd0     ; // pidB set_point
        pidB_kp                <=  14'd0     ; // pidB proportional constant
        pidB_ki                <=  14'd0     ; // pidB integral constant
        pidB_kd                <=  14'd0     ; // pidB derivative constant
        pidB_ctrl              <=   3'd0     ; // pidB control: [ pidB_ifreeze: integrator freeze , pidB_freeze: output freeze , pidB_irst:integrator reset]
        aux_A                  <=  14'd0     ; // auxiliar value of 14 bits
        aux_B                  <=  14'd0     ; // auxiliar value of 14 bits
    end else begin
        if (sys_wen) begin
            if (sys_addr[19:0]==20'h00000)  oscA_sw               <=  sys_wdata[ 5-1: 0] ; // switch for muxer oscA
            if (sys_addr[19:0]==20'h00004)  oscB_sw               <=  sys_wdata[ 5-1: 0] ; // switch for muxer oscB
            if (sys_addr[19:0]==20'h00008)  osc_ctrl              <=  sys_wdata[ 2-1: 0] ; // oscilloscope control // [osc2_filt_off,osc1_filt_off]
            if (sys_addr[19:0]==20'h0000C)  trig_sw               <=  sys_wdata[ 8-1: 0] ; // Select the external trigger signal
            if (sys_addr[19:0]==20'h00010)  out1_sw               <=  sys_wdata[ 4-1: 0] ; // switch for muxer out1
            if (sys_addr[19:0]==20'h00014)  out2_sw               <=  sys_wdata[ 4-1: 0] ; // switch for muxer out2
            if (sys_addr[19:0]==20'h00018)  lock_control          <=  sys_wdata[11-1: 0] ; // lock_control help
          //if (sys_addr[19:0]==20'h0001C)  lock_feedback         <=  sys_wdata[11-1: 0] ; // lock_control feedback
            if (sys_addr[19:0]==20'h00020)  lock_trig_val         <=  sys_wdata[14-1: 0] ; // if lock_control ?? , this vals sets the voltage threshold that turns on the lock
            if (sys_addr[19:0]==20'h00024)  lock_trig_time        <=  sys_wdata[32-1: 0] ; // if lock_control ?? , this vals sets the time threshold that turns on the lock
            if (sys_addr[19:0]==20'h00028)  lock_trig_sw          <=  sys_wdata[ 4-1: 0] ; // selects signal for trigger
            if (sys_addr[19:0]==20'h0002C)  rl_error_threshold    <=  sys_wdata[13-1: 0] ; // Threshold for error signal. Launchs relock when |error| > rl_error_threshold
            if (sys_addr[19:0]==20'h00030)  rl_signal_sw          <=  sys_wdata[ 3-1: 0] ; // selects signal for relock trigger
            if (sys_addr[19:0]==20'h00034)  rl_signal_threshold   <=  sys_wdata[14-1: 0] ; // Threshold for signal. Launchs relock when signal < rl_signal_threshold
            if (sys_addr[19:0]==20'h00038)  rl_config             <=  sys_wdata[ 3-1: 0] ; // Relock enable. [relock_reset,enable_signal_th,enable_error_th] 
          //if (sys_addr[19:0]==20'h0003C)  rl_state              <=  sys_wdata[ 5-1: 0] ; // Relock state: [state:idle|searching|failed,signal_fail,error_fail,locked] 
            if (sys_addr[19:0]==20'h00040)  sf_jumpA              <=  sys_wdata[14-1: 0] ; // Step function measure jump value for ctrl_A
            if (sys_addr[19:0]==20'h00044)  sf_jumpB              <=  sys_wdata[14-1: 0] ; // Step function measure jump value for ctrl_B
            if (sys_addr[19:0]==20'h00048)  sf_config             <=  sys_wdata[ 5-1: 0] ; // Step function configuration. [pidB_ifreeze,pidB_freeze,pidA_ifreeze,pidA_freeze,start] 
            if (sys_addr[19:0]==20'h0004C)  signal_sw             <=  sys_wdata[ 3-1: 0] ; // Input selector for signal_i
          //if (sys_addr[19:0]==20'h00050)  signal_i              <=  sys_wdata[14-1: 0] ; // signal for demodulation
            if (sys_addr[19:0]==20'h00054)  sg_amp0               <=  sys_wdata[ 5-1: 0] ; // amplification of Xo, Yo
            if (sys_addr[19:0]==20'h00058)  sg_amp1               <=  sys_wdata[ 4-1: 0] ; // amplification F1o
            if (sys_addr[19:0]==20'h0005C)  sg_amp2               <=  sys_wdata[ 4-1: 0] ; // amplification of F2o
            if (sys_addr[19:0]==20'h00060)  sg_amp3               <=  sys_wdata[ 4-1: 0] ; // amplification of F3o
            if (sys_addr[19:0]==20'h00064)  lpf_F0                <=  sys_wdata[ 6-1: 0] ; // Low Pass Filter of X, Y
            if (sys_addr[19:0]==20'h00068)  lpf_F1                <=  sys_wdata[ 6-1: 0] ; // Low Pass Filter F1
            if (sys_addr[19:0]==20'h0006C)  lpf_F2                <=  sys_wdata[ 6-1: 0] ; // Low Pass Filter of F2
            if (sys_addr[19:0]==20'h00070)  lpf_F3                <=  sys_wdata[ 6-1: 0] ; // Low Pass Filter of F3
            if (sys_addr[19:0]==20'h00074)  error_sw              <=  sys_wdata[ 3-1: 0] ; // select error signal
            if (sys_addr[19:0]==20'h00078)  error_offset          <=  sys_wdata[14-1: 0] ; // offset for the error signal
          //if (sys_addr[19:0]==20'h0007C)  error                 <=  sys_wdata[14-1: 0] ; // error signal value
          //if (sys_addr[19:0]==20'h00080)  error_mean            <=  sys_wdata[32-1: 0] ; // 1 sec error mean val
          //if (sys_addr[19:0]==20'h00084)  error_std             <=  sys_wdata[32-1: 0] ; // 1 sec error square sum val
            if (sys_addr[19:0]==20'h00088)  mod_out1              <=  sys_wdata[14-1: 0] ; // Modulation amplitud for out1
            if (sys_addr[19:0]==20'h0008C)  mod_out2              <=  sys_wdata[14-1: 0] ; // Modulation amplitud for out2
            if (sys_addr[19:0]==20'h00090)  gen_mod_phase         <=  sys_wdata[12-1: 0] ; // phase relation of cos_?f signals
            if (sys_addr[19:0]==20'h00094)  gen_mod_hp            <=  sys_wdata[14-1: 0] ; // harmonic period set
          //if (sys_addr[19:0]==20'h00098)  ramp_A                <=  sys_wdata[14-1: 0] ; // ramp signal A
          //if (sys_addr[19:0]==20'h0009C)  ramp_B                <=  sys_wdata[14-1: 0] ; // ramp signal B
            if (sys_addr[19:0]==20'h000A0)  ramp_step             <=  sys_wdata[32-1: 0] ; // period of the triangular ramp signal
            if (sys_addr[19:0]==20'h000A4)  ramp_low_lim          <=  sys_wdata[14-1: 0] ; // ramp low limit
            if (sys_addr[19:0]==20'h000A8)  ramp_hig_lim          <=  sys_wdata[14-1: 0] ; // ramp high limit
            if (sys_addr[19:0]==20'h000AC)  ramp_reset            <= |sys_wdata[32-1: 0] ; // ramp reset config
            if (sys_addr[19:0]==20'h000B0)  ramp_enable           <= |sys_wdata[32-1: 0] ; // ramp enable/disable switch
            if (sys_addr[19:0]==20'h000B4)  ramp_direction        <= |sys_wdata[32-1: 0] ; // ramp starting direction (up/down)
            if (sys_addr[19:0]==20'h000B8)  ramp_B_factor         <=  sys_wdata[14-1: 0] ; // proportional factor ramp_A/ramp_B. // ramp_B=ramp_A*ramp_B_factor/4096
          //if (sys_addr[19:0]==20'h000BC)  sin_ref               <=  sys_wdata[14-1: 0] ; // lock-in modulation sinus harmonic reference
          //if (sys_addr[19:0]==20'h000C0)  cos_ref               <=  sys_wdata[14-1: 0] ; // lock-in modulation cosinus harmonic reference
          //if (sys_addr[19:0]==20'h000C4)  cos_1f                <=  sys_wdata[14-1: 0] ; // lock-in modulation sinus harmonic signal with phase relation to reference
          //if (sys_addr[19:0]==20'h000C8)  cos_2f                <=  sys_wdata[14-1: 0] ; // lock-in modulation sinus harmonic signal with phase relation to reference and double frequency
          //if (sys_addr[19:0]==20'h000CC)  cos_3f                <=  sys_wdata[14-1: 0] ; // lock-in modulation sinus harmonic signal with phase relation to reference and triple frequency
          //if (sys_addr[19:0]==20'h000D0)  in1                   <=  sys_wdata[14-1: 0] ; // Input signal IN1
          //if (sys_addr[19:0]==20'h000D4)  in2                   <=  sys_wdata[14-1: 0] ; // Input signal IN2
          //if (sys_addr[19:0]==20'h000D8)  out1                  <=  sys_wdata[14-1: 0] ; // signal for RP RF DAC Out1
          //if (sys_addr[19:0]==20'h000DC)  out2                  <=  sys_wdata[14-1: 0] ; // signal for RP RF DAC Out2
          //if (sys_addr[19:0]==20'h000E0)  oscA                  <=  sys_wdata[14-1: 0] ; // signal for Oscilloscope Channel A
          //if (sys_addr[19:0]==20'h000E4)  oscB                  <=  sys_wdata[14-1: 0] ; // signal for Oscilloscope Channel B
          //if (sys_addr[19:0]==20'h000E8)  X_28                  <=  sys_wdata[28-1: 0] ; // Demodulated signal from sin_ref
          //if (sys_addr[19:0]==20'h000EC)  Y_28                  <=  sys_wdata[28-1: 0] ; // Demodulated signal from cos_ref
          //if (sys_addr[19:0]==20'h000F0)  F1_28                 <=  sys_wdata[28-1: 0] ; // Demodulated signal from cos_1f
          //if (sys_addr[19:0]==20'h000F4)  F2_28                 <=  sys_wdata[28-1: 0] ; // Demodulated signal from cos_2f
          //if (sys_addr[19:0]==20'h000F8)  F3_28                 <=  sys_wdata[28-1: 0] ; // Demodulated signal from cos_3f
          //if (sys_addr[19:0]==20'h000FC)  cnt_clk               <=  sys_wdata[32-1: 0] ; // Clock count
          //if (sys_addr[19:0]==20'h00100)  cnt_clk2              <=  sys_wdata[32-1: 0] ; // Clock count
            if (sys_addr[19:0]==20'h00104)  read_ctrl             <=  sys_wdata[ 3-1: 0] ; // [unused,start_clk,Freeze]
            if (sys_addr[19:0]==20'h00108)  pidA_sw               <=  sys_wdata[ 5-1: 0] ; // switch selector for pidA input
            if (sys_addr[19:0]==20'h0010C)  pidA_PSR              <=  sys_wdata[ 3-1: 0] ; // pidA PSR
            if (sys_addr[19:0]==20'h00110)  pidA_ISR              <=  sys_wdata[ 4-1: 0] ; // pidA ISR
            if (sys_addr[19:0]==20'h00114)  pidA_DSR              <=  sys_wdata[ 3-1: 0] ; // pidA DSR
            if (sys_addr[19:0]==20'h00118)  pidA_SAT              <=  sys_wdata[14-1: 0] ; // pidA saturation control
            if (sys_addr[19:0]==20'h0011C)  pidA_sp               <=  sys_wdata[14-1: 0] ; // pidA set_point
            if (sys_addr[19:0]==20'h00120)  pidA_kp               <=  sys_wdata[14-1: 0] ; // pidA proportional constant
            if (sys_addr[19:0]==20'h00124)  pidA_ki               <=  sys_wdata[14-1: 0] ; // pidA integral constant
            if (sys_addr[19:0]==20'h00128)  pidA_kd               <=  sys_wdata[14-1: 0] ; // pidA derivative constant
          //if (sys_addr[19:0]==20'h0012C)  pidA_in               <=  sys_wdata[14-1: 0] ; // pidA input
          //if (sys_addr[19:0]==20'h00130)  pidA_out              <=  sys_wdata[14-1: 0] ; // pidA output
            if (sys_addr[19:0]==20'h00134)  pidA_ctrl             <=  sys_wdata[ 3-1: 0] ; // pidA control: [ pidA_ifreeze: integrator freeze , pidA_freeze: output freeze , pidA_irst:integrator reset]
          //if (sys_addr[19:0]==20'h00138)  ctrl_A                <=  sys_wdata[14-1: 0] ; // control_A: pidA_out + ramp_A
            if (sys_addr[19:0]==20'h0013C)  pidB_sw               <=  sys_wdata[ 5-1: 0] ; // switch selector for pidB input
            if (sys_addr[19:0]==20'h00140)  pidB_PSR              <=  sys_wdata[ 3-1: 0] ; // pidB PSR
            if (sys_addr[19:0]==20'h00144)  pidB_ISR              <=  sys_wdata[ 4-1: 0] ; // pidB ISR
            if (sys_addr[19:0]==20'h00148)  pidB_DSR              <=  sys_wdata[ 3-1: 0] ; // pidB DSR
            if (sys_addr[19:0]==20'h0014C)  pidB_SAT              <=  sys_wdata[14-1: 0] ; // pidB saturation control
            if (sys_addr[19:0]==20'h00150)  pidB_sp               <=  sys_wdata[14-1: 0] ; // pidB set_point
            if (sys_addr[19:0]==20'h00154)  pidB_kp               <=  sys_wdata[14-1: 0] ; // pidB proportional constant
            if (sys_addr[19:0]==20'h00158)  pidB_ki               <=  sys_wdata[14-1: 0] ; // pidB integral constant
            if (sys_addr[19:0]==20'h0015C)  pidB_kd               <=  sys_wdata[14-1: 0] ; // pidB derivative constant
          //if (sys_addr[19:0]==20'h00160)  pidB_in               <=  sys_wdata[14-1: 0] ; // pidB input
          //if (sys_addr[19:0]==20'h00164)  pidB_out              <=  sys_wdata[14-1: 0] ; // pidB output
            if (sys_addr[19:0]==20'h00168)  pidB_ctrl             <=  sys_wdata[ 3-1: 0] ; // pidB control: [ pidB_ifreeze: integrator freeze , pidB_freeze: output freeze , pidB_irst:integrator reset]
          //if (sys_addr[19:0]==20'h0016C)  ctrl_B                <=  sys_wdata[14-1: 0] ; // control_B: pidA_out + ramp_B
            if (sys_addr[19:0]==20'h00170)  aux_A                 <=  sys_wdata[14-1: 0] ; // auxiliar value of 14 bits
            if (sys_addr[19:0]==20'h00174)  aux_B                 <=  sys_wdata[14-1: 0] ; // auxiliar value of 14 bits
        end
    end
    //---------------------------------------------------------------------------------
    // FPGA --> MEMORIA --> SO
    wire sys_en;
    assign sys_en = sys_wen | sys_ren;
    
    always @(posedge clk, posedge rst)
    if (rst) begin
        sys_err <= 1'b0  ;
        sys_ack <= 1'b0  ;
    end else begin
        sys_err <= 1'b0 ;
        
        casez (sys_addr[19:0])
            20'h00000 : begin sys_ack <= sys_en;  sys_rdata <= {  27'b0                   ,          oscA_sw  }; end // switch for muxer oscA
            20'h00004 : begin sys_ack <= sys_en;  sys_rdata <= {  27'b0                   ,          oscB_sw  }; end // switch for muxer oscB
            20'h00008 : begin sys_ack <= sys_en;  sys_rdata <= {  30'b0                   ,         osc_ctrl  }; end // oscilloscope control // [osc2_filt_off,osc1_filt_off]
            20'h0000C : begin sys_ack <= sys_en;  sys_rdata <= {  24'b0                   ,          trig_sw  }; end // Select the external trigger signal
            20'h00010 : begin sys_ack <= sys_en;  sys_rdata <= {  28'b0                   ,          out1_sw  }; end // switch for muxer out1
            20'h00014 : begin sys_ack <= sys_en;  sys_rdata <= {  28'b0                   ,          out2_sw  }; end // switch for muxer out2
            20'h00018 : begin sys_ack <= sys_en;  sys_rdata <= {  21'b0                   ,     lock_control  }; end // lock_control help
            20'h0001C : begin sys_ack <= sys_en;  sys_rdata <= {  21'b0                   ,    lock_feedback  }; end // lock_control feedback
            20'h00020 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{lock_trig_val[13]}} ,    lock_trig_val  }; end // if lock_control ?? , this vals sets the voltage threshold that turns on the lock
            20'h00024 : begin sys_ack <= sys_en;  sys_rdata <=                                lock_trig_time   ; end // if lock_control ?? , this vals sets the time threshold that turns on the lock
            20'h00028 : begin sys_ack <= sys_en;  sys_rdata <= {  28'b0                   ,     lock_trig_sw  }; end // selects signal for trigger
            20'h0002C : begin sys_ack <= sys_en;  sys_rdata <= {  19'b0                   ,  rl_error_threshold  }; end // Threshold for error signal. Launchs relock when |error| > rl_error_threshold
            20'h00030 : begin sys_ack <= sys_en;  sys_rdata <= {  29'b0                   ,     rl_signal_sw  }; end // selects signal for relock trigger
            20'h00034 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{rl_signal_threshold[13]}} ,  rl_signal_threshold  }; end // Threshold for signal. Launchs relock when signal < rl_signal_threshold
            20'h00038 : begin sys_ack <= sys_en;  sys_rdata <= {  29'b0                   ,        rl_config  }; end // Relock enable. [relock_reset,enable_signal_th,enable_error_th] 
            20'h0003C : begin sys_ack <= sys_en;  sys_rdata <= {  27'b0                   ,         rl_state  }; end // Relock state: [state:idle|searching|failed,signal_fail,error_fail,locked] 
            20'h00040 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{sf_jumpA[13]}}      ,         sf_jumpA  }; end // Step function measure jump value for ctrl_A
            20'h00044 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{sf_jumpB[13]}}      ,         sf_jumpB  }; end // Step function measure jump value for ctrl_B
            20'h00048 : begin sys_ack <= sys_en;  sys_rdata <= {  27'b0                   ,        sf_config  }; end // Step function configuration. [pidB_ifreeze,pidB_freeze,pidA_ifreeze,pidA_freeze,start] 
            20'h0004C : begin sys_ack <= sys_en;  sys_rdata <= {  29'b0                   ,        signal_sw  }; end // Input selector for signal_i
            20'h00050 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{signal_i[13]}}      ,         signal_i  }; end // signal for demodulation
            20'h00054 : begin sys_ack <= sys_en;  sys_rdata <= {  27'b0                   ,          sg_amp0  }; end // amplification of Xo, Yo
            20'h00058 : begin sys_ack <= sys_en;  sys_rdata <= {  28'b0                   ,          sg_amp1  }; end // amplification F1o
            20'h0005C : begin sys_ack <= sys_en;  sys_rdata <= {  28'b0                   ,          sg_amp2  }; end // amplification of F2o
            20'h00060 : begin sys_ack <= sys_en;  sys_rdata <= {  28'b0                   ,          sg_amp3  }; end // amplification of F3o
            20'h00064 : begin sys_ack <= sys_en;  sys_rdata <= {  26'b0                   ,           lpf_F0  }; end // Low Pass Filter of X, Y
            20'h00068 : begin sys_ack <= sys_en;  sys_rdata <= {  26'b0                   ,           lpf_F1  }; end // Low Pass Filter F1
            20'h0006C : begin sys_ack <= sys_en;  sys_rdata <= {  26'b0                   ,           lpf_F2  }; end // Low Pass Filter of F2
            20'h00070 : begin sys_ack <= sys_en;  sys_rdata <= {  26'b0                   ,           lpf_F3  }; end // Low Pass Filter of F3
            20'h00074 : begin sys_ack <= sys_en;  sys_rdata <= {  29'b0                   ,         error_sw  }; end // select error signal
            20'h00078 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{error_offset[13]}}  ,     error_offset  }; end // offset for the error signal
            20'h0007C : begin sys_ack <= sys_en;  sys_rdata <= {  {18{error_reg[13]}}     ,        error_reg  }; end // error signal value
            20'h00080 : begin sys_ack <= sys_en;  sys_rdata <=                                    error_mean   ; end // 1 sec error mean val
            20'h00084 : begin sys_ack <= sys_en;  sys_rdata <=                                     error_std   ; end // 1 sec error square sum val
            20'h00088 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{mod_out1[13]}}      ,         mod_out1  }; end // Modulation amplitud for out1
            20'h0008C : begin sys_ack <= sys_en;  sys_rdata <= {  {18{mod_out2[13]}}      ,         mod_out2  }; end // Modulation amplitud for out2
            20'h00090 : begin sys_ack <= sys_en;  sys_rdata <= {  20'b0                   ,    gen_mod_phase  }; end // phase relation of cos_?f signals
            20'h00094 : begin sys_ack <= sys_en;  sys_rdata <= {  18'b0                   ,       gen_mod_hp  }; end // harmonic period set
            20'h00098 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{ramp_A[13]}}        ,           ramp_A  }; end // ramp signal A
            20'h0009C : begin sys_ack <= sys_en;  sys_rdata <= {  {18{ramp_B[13]}}        ,           ramp_B  }; end // ramp signal B
            20'h000A0 : begin sys_ack <= sys_en;  sys_rdata <=                                     ramp_step   ; end // period of the triangular ramp signal
            20'h000A4 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{ramp_low_lim[13]}}  ,     ramp_low_lim  }; end // ramp low limit
            20'h000A8 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{ramp_hig_lim[13]}}  ,     ramp_hig_lim  }; end // ramp high limit
            20'h000AC : begin sys_ack <= sys_en;  sys_rdata <= {  31'b0                   ,       ramp_reset  }; end // ramp reset config
            20'h000B0 : begin sys_ack <= sys_en;  sys_rdata <= {  31'b0                   ,      ramp_enable  }; end // ramp enable/disable switch
            20'h000B4 : begin sys_ack <= sys_en;  sys_rdata <= {  31'b0                   ,   ramp_direction  }; end // ramp starting direction (up/down)
            20'h000B8 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{ramp_B_factor[13]}} ,    ramp_B_factor  }; end // proportional factor ramp_A/ramp_B. // ramp_B=ramp_A*ramp_B_factor/4096
            20'h000BC : begin sys_ack <= sys_en;  sys_rdata <= {  {18{sin_ref[13]}}       ,          sin_ref  }; end // lock-in modulation sinus harmonic reference
            20'h000C0 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{cos_ref[13]}}       ,          cos_ref  }; end // lock-in modulation cosinus harmonic reference
            20'h000C4 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{cos_1f[13]}}        ,           cos_1f  }; end // lock-in modulation sinus harmonic signal with phase relation to reference
            20'h000C8 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{cos_2f[13]}}        ,           cos_2f  }; end // lock-in modulation sinus harmonic signal with phase relation to reference and double frequency
            20'h000CC : begin sys_ack <= sys_en;  sys_rdata <= {  {18{cos_3f[13]}}        ,           cos_3f  }; end // lock-in modulation sinus harmonic signal with phase relation to reference and triple frequency
            20'h000D0 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{in1[13]}}           ,              in1  }; end // Input signal IN1
            20'h000D4 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{in2[13]}}           ,              in2  }; end // Input signal IN2
            20'h000D8 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{out1[13]}}          ,             out1  }; end // signal for RP RF DAC Out1
            20'h000DC : begin sys_ack <= sys_en;  sys_rdata <= {  {18{out2[13]}}          ,             out2  }; end // signal for RP RF DAC Out2
            20'h000E0 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{oscA[13]}}          ,             oscA  }; end // signal for Oscilloscope Channel A
            20'h000E4 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{oscB[13]}}          ,             oscB  }; end // signal for Oscilloscope Channel B
            20'h000E8 : begin sys_ack <= sys_en;  sys_rdata <= {  { 4{X_28_reg[27]}}      ,         X_28_reg  }; end // Demodulated signal from sin_ref
            20'h000EC : begin sys_ack <= sys_en;  sys_rdata <= {  { 4{Y_28_reg[27]}}      ,         Y_28_reg  }; end // Demodulated signal from cos_ref
            20'h000F0 : begin sys_ack <= sys_en;  sys_rdata <= {  { 4{F1_28_reg[27]}}     ,        F1_28_reg  }; end // Demodulated signal from cos_1f
            20'h000F4 : begin sys_ack <= sys_en;  sys_rdata <= {  { 4{F2_28_reg[27]}}     ,        F2_28_reg  }; end // Demodulated signal from cos_2f
            20'h000F8 : begin sys_ack <= sys_en;  sys_rdata <= {  { 4{F3_28_reg[27]}}     ,        F3_28_reg  }; end // Demodulated signal from cos_3f
            20'h000FC : begin sys_ack <= sys_en;  sys_rdata <=                                       cnt_clk   ; end // Clock count
            20'h00100 : begin sys_ack <= sys_en;  sys_rdata <=                                      cnt_clk2   ; end // Clock count
            20'h00104 : begin sys_ack <= sys_en;  sys_rdata <= {  29'b0                   ,        read_ctrl  }; end // [unused,start_clk,Freeze]
            20'h00108 : begin sys_ack <= sys_en;  sys_rdata <= {  27'b0                   ,          pidA_sw  }; end // switch selector for pidA input
            20'h0010C : begin sys_ack <= sys_en;  sys_rdata <= {  29'b0                   ,         pidA_PSR  }; end // pidA PSR
            20'h00110 : begin sys_ack <= sys_en;  sys_rdata <= {  28'b0                   ,         pidA_ISR  }; end // pidA ISR
            20'h00114 : begin sys_ack <= sys_en;  sys_rdata <= {  29'b0                   ,         pidA_DSR  }; end // pidA DSR
            20'h00118 : begin sys_ack <= sys_en;  sys_rdata <= {  18'b0                   ,         pidA_SAT  }; end // pidA saturation control
            20'h0011C : begin sys_ack <= sys_en;  sys_rdata <= {  {18{pidA_sp[13]}}       ,          pidA_sp  }; end // pidA set_point
            20'h00120 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{pidA_kp[13]}}       ,          pidA_kp  }; end // pidA proportional constant
            20'h00124 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{pidA_ki[13]}}       ,          pidA_ki  }; end // pidA integral constant
            20'h00128 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{pidA_kd[13]}}       ,          pidA_kd  }; end // pidA derivative constant
            20'h0012C : begin sys_ack <= sys_en;  sys_rdata <= {  {18{pidA_in[13]}}       ,          pidA_in  }; end // pidA input
            20'h00130 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{pidA_out[13]}}      ,         pidA_out  }; end // pidA output
            20'h00134 : begin sys_ack <= sys_en;  sys_rdata <= {  29'b0                   ,        pidA_ctrl  }; end // pidA control: [ pidA_ifreeze: integrator freeze , pidA_freeze: output freeze , pidA_irst:integrator reset]
            20'h00138 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{ctrl_A_reg[13]}}    ,       ctrl_A_reg  }; end // control_A: pidA_out + ramp_A
            20'h0013C : begin sys_ack <= sys_en;  sys_rdata <= {  27'b0                   ,          pidB_sw  }; end // switch selector for pidB input
            20'h00140 : begin sys_ack <= sys_en;  sys_rdata <= {  29'b0                   ,         pidB_PSR  }; end // pidB PSR
            20'h00144 : begin sys_ack <= sys_en;  sys_rdata <= {  28'b0                   ,         pidB_ISR  }; end // pidB ISR
            20'h00148 : begin sys_ack <= sys_en;  sys_rdata <= {  29'b0                   ,         pidB_DSR  }; end // pidB DSR
            20'h0014C : begin sys_ack <= sys_en;  sys_rdata <= {  18'b0                   ,         pidB_SAT  }; end // pidB saturation control
            20'h00150 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{pidB_sp[13]}}       ,          pidB_sp  }; end // pidB set_point
            20'h00154 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{pidB_kp[13]}}       ,          pidB_kp  }; end // pidB proportional constant
            20'h00158 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{pidB_ki[13]}}       ,          pidB_ki  }; end // pidB integral constant
            20'h0015C : begin sys_ack <= sys_en;  sys_rdata <= {  {18{pidB_kd[13]}}       ,          pidB_kd  }; end // pidB derivative constant
            20'h00160 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{pidB_in[13]}}       ,          pidB_in  }; end // pidB input
            20'h00164 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{pidB_out[13]}}      ,         pidB_out  }; end // pidB output
            20'h00168 : begin sys_ack <= sys_en;  sys_rdata <= {  29'b0                   ,        pidB_ctrl  }; end // pidB control: [ pidB_ifreeze: integrator freeze , pidB_freeze: output freeze , pidB_irst:integrator reset]
            20'h0016C : begin sys_ack <= sys_en;  sys_rdata <= {  {18{ctrl_B_reg[13]}}    ,       ctrl_B_reg  }; end // control_B: pidA_out + ramp_B
            20'h00170 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{aux_A[13]}}         ,            aux_A  }; end // auxiliar value of 14 bits
            20'h00174 : begin sys_ack <= sys_en;  sys_rdata <= {  {18{aux_B[13]}}         ,            aux_B  }; end // auxiliar value of 14 bits
            default   : begin sys_ack <= sys_en;  sys_rdata <=  32'h0        ; end
        endcase
    end
    // [FPGA MEMORY DOCK END]

endmodule
