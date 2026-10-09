`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company:
// Engineer:
//
// Create Date: 22.02.2017 11:41:25
// Design Name:
// Module Name: lock_ctrl
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


module lock_ctrl
    (
    input clk,rst,
    // inputs
    input         [10-1:0] lock_ctrl,
    input  signed [14-1:0] signal,
    input                  ramp_trigger,
    input         [32-1:0] time_threshold,
    input  signed [14-1:0] level_threshold,
    input                  level_rising_trigger,
    // outputs
    output                 ramp_enable,
    output                 pidA_enable,
    output                 pidB_enable,
    output                 lock_ctrl_trig,
    output        [16-1:0] lock_status
    );

    /** lock_ctrl (register lock_control) is COMMAND + CONFIGURATION: this module never
     *  needs it to be rewritten (v2.3.13, see doc/lock_control.md). Bits:
     *
     * lock_ctrl[ 0] --> lock_now         : lock request, immediate (0->1 edge locks)
     * lock_ctrl[ 1] --> launch_lock      : lock request on trigger (0->1 edge arms)
     *                                      [1:0]==00 releases the lock (back to IDLE)
     * lock_ctrl[ 2] --> pidB_enable_ctrl --|   manual (open loop) enables, effective in
     * lock_ctrl[ 3] --> pidA_enable_ctrl   |-> IDLE and ARMED. A change while LOCKED
     * lock_ctrl[ 4] --> ramp_enable_ctrl --|   releases the lock (manual override)
     * lock_ctrl[ 5] --> set_pidB_enable --|
     * lock_ctrl[ 6] --> set_pidA_enable   |--> enables while LOCKED
     * lock_ctrl[ 7] --> set_ramp_enable --|
     * lock_ctrl[ 8] --> trig_time        : time trigger
     * lock_ctrl[ 9] --> trig_val         : level trigger (both: level after time)
     * lock_trig_rise (lock_control[10])  : level_rising_trigger input
     *
     * lock_status (read only):
     *   [0] armed, [1] locked, [2] pidB_enable, [3] pidA_enable, [4] ramp_enable (effective),
     *   [7:5] 0, [15:8] number of entries into LOCKED (modulo 256)
     **/

    localparam ST_IDLE   = 2'd0 ,
               ST_ARMED  = 2'd1 ,
               ST_LOCKED = 2'd2 ;

    // previous value of the command/configuration bits: edges of lock_now / launch_lock and
    // changes of the manual enables
    reg  [5-1:0] ctrl_last;

    always @(posedge clk)
        if (rst) ctrl_last  <=  5'b0 ;
        else     ctrl_last  <=  lock_ctrl[4:0] ;

    wire   lock_now_rise, launch_rise, release_req, manual_change;
    assign lock_now_rise  =  lock_ctrl[0] & ~ctrl_last[0] ;
    assign launch_rise    =  lock_ctrl[1] & ~ctrl_last[1] ;
    assign release_req    = ~(|lock_ctrl[1:0]) ;
    assign manual_change  =  |(lock_ctrl[4:2] ^ ctrl_last[4:2]) ;

    wire   seek_time_trig,seek_level_trig;
    assign seek_time_trig  = lock_ctrl[8] ;  // time trigger configured
    assign seek_level_trig = lock_ctrl[9] ;  // level trigger configured


    // counter for time trigger
    reg  [31-1:0] cnt ;
    wire [32-1:0] cnt_next ;

    always @(posedge clk, posedge rst)
        if (rst) cnt  <=   31'b0   ;
        else     cnt  <=  cnt_next[31-1:0] ;

    // counter is synchronized with gen_ramp signal
    assign cnt_next = ramp_trigger ? 32'b0 : cnt+1'b1 ;



    // save last val of signal (useful to get level trigger slope condition)
    reg  signed   [14-1:0] signal_last,signal_now;

    always @(posedge clk) begin
        if (rst) begin
            signal_last  <=   14'b0   ;
            signal_now   <=   14'b0   ;
        end
        else begin
            signal_last  <=   signal_now ;
            signal_now   <=   signal     ;
        end
    end


    // Trigger conditions (same as v2.3.12)
    wire  trigger,time_trigger,level_trigger,both_trigger;
    wire  now_eg_th,last_lt_th;

    // Time trigger
    assign time_trigger  = (cnt==time_threshold[31-1:0]) & seek_time_trig & (~seek_level_trig) ;

    /* Level trigger: if signal is equal or greater (less) than threshold
                      and was less (equal or greater) in the last value
                      then fires trigger
    */
    assign now_eg_th        = signal_now>=level_threshold;
    assign last_lt_th       = signal_last<level_threshold;
    assign level_trigger    = ( ~ ( ( now_eg_th^last_lt_th  ) | ( last_lt_th^level_rising_trigger ) ) )
                              & seek_level_trig ;

    // time+level trigger: if time trigger condition was already met, then fire trigger when level condition is met
    assign both_trigger     = level_trigger & (cnt>=time_threshold[31-1:0]) & seek_time_trig;

    assign trigger          = time_trigger | (level_trigger&(~seek_time_trig)) | both_trigger;


    // State machine: IDLE -> ARMED -> LOCKED, executed here without any write from the PS
    reg  [ 2-1:0] state;
    reg  [ 8-1:0] lock_cnt;
    reg           lock_trig_r;
    reg  [ 2-1:0] state_next;

    always @(*) begin
        state_next = state ;
        case (state)
            ST_IDLE   : if      (lock_now_rise)              state_next = ST_LOCKED ;
                        else if (launch_rise)                state_next = ST_ARMED  ;
            ST_ARMED  : if      (release_req)                state_next = ST_IDLE   ;
                        else if (lock_now_rise | trigger)    state_next = ST_LOCKED ;
            ST_LOCKED : if      (release_req|manual_change)  state_next = ST_IDLE   ;
            default   :                                      state_next = ST_IDLE   ;
        endcase
    end

    wire   enter_lock;
    assign enter_lock = (state_next==ST_LOCKED) & (state!=ST_LOCKED) ;

    always @(posedge clk) begin
        if (rst) begin
            state        <=  ST_IDLE ;
            lock_cnt     <=  8'b0    ;
            lock_trig_r  <=  1'b0    ;
        end
        else begin
            state        <=  state_next ;
            lock_trig_r  <=  enter_lock ;
            if (enter_lock)
                lock_cnt <=  lock_cnt + 1'b1 ;
        end
    end

    wire   locked,armed;
    assign locked         = (state==ST_LOCKED) ;
    assign armed          = (state==ST_ARMED ) ;

    // one clock pulse when the lock closes (oscilloscope trigger source)
    assign lock_ctrl_trig = lock_trig_r ;

    // Outputs: effective enables
    assign ramp_enable      = locked ?  lock_ctrl[7] :  lock_ctrl[4]   ;
    assign pidA_enable      = locked ?  lock_ctrl[6] :  lock_ctrl[3]   ;
    assign pidB_enable      = locked ?  lock_ctrl[5] :  lock_ctrl[2]   ;

    assign lock_status      = { lock_cnt , 3'b0 , ramp_enable , pidA_enable , pidB_enable , locked , armed } ;


endmodule



/*
lock_ctrl NAME (
    .clk(clk),  .rst(rst),
    // inputs
    .lock_ctrl            ( lock_state         ),
    .signal               ( lock_ctrl_signal   ),
    .ramp_trigger         ( ramp_trig          ),
    .time_threshold       ( lock_trig_time_val ),
    .level_threshold      ( lock_trig_val      ),
    .level_rising_trigger ( lock_trig_rise     ),
    // outputs
    .ramp_enable          ( ramp_enable_ctrl   ),
    .pidA_enable          ( pidA_enable_ctrl   ),
    .pidB_enable          ( pidB_enable_ctrl   ),
    .lock_ctrl_trig       ( lock_ctrl_trig     ),
    .lock_status          ( lock_status        )
);
*/
