`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Module Name: shift_sat14
//
// v2.3.19: amplification (sg_amp) + output saturation of the lock-in channels in one step.
//
// Same result, bit by bit, as the chain used up to v2.3.18 in lock.v:
//
//     w   = in <<< sh                                   (W bits, sign extended, upper bits lost)
//     o1  = satprotect2 #(.Ri(W),.Ro(RO)) ( w )          (RO bits)
//     out = satprotect2 #(.Ri(17),.Ro(14)) ( o1[RO-1:RO-17] )
//
// (Xo/Yo: RI=38, W=53, RO=38 ; F1o/F2o/F3o: RI=28, W=43, RO=28).
// The two saturations together keep w[RO-4:RO-17] when w fits in RO-3 bits (that is, when the
// bits w[W-1:RO-4] are all equal) and give the 14 bit limit with the sign of w[W-1] otherwise:
//   - o1 saturates  <=> w[W-1:RO-1] not all equal  -> o1 = limit with sign w[W-1] -> out = limit
//   - o1 = w[RO-1:0] and o1[RO-1:RO-17] saturates <=> w[RO-1:RO-4] not all equal -> limit with
//     sign w[RO-1] = w[W-1]
//   - otherwise out = w[RO-4:RO-17]
// Fewer logic levels than the two cascaded saturations (one test of 19 bits instead of two tests in
// series). Checked against the old chain in test/lock_latency_sim.sh (old and new lock.v side by side).
//////////////////////////////////////////////////////////////////////////////////

module shift_sat14 #(
   parameter     RI = 38,   // input width
   parameter     W  = 53,   // width of the shifted value
   parameter     RO = 38,   // output width of the first saturation
   parameter     SB = 5     // width of the shift
)
(
    input  signed [RI-1:0] in,    // input signal
    input         [SB-1:0] sh,    // amplification: shift to the left
    output signed [  14-1:0] out  // output signal
    );

    wire signed [W-1:0] w;
    wire                fits;

    assign w    = in <<< sh ;
    assign fits = ( &w[W-1:RO-4] ) | ( ~|w[W-1:RO-4] ) ;
    assign out  = fits ? w[RO-4:RO-17] : { w[W-1] , {13{~w[W-1]}} } ;

endmodule

/*
Instantiation example:

shift_sat14 #(.RI(38),.W(53),.RO(38),.SB(5)) i_shift_sat14_Xo ( .in( cos_ref_lpf2 ), .sh( sg_amp0 ), .out( Xo_w ) );
*/
