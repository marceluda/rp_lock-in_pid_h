`timescale 1ns / 1ps
// v2.3.21: periods that Reset Zoom uses (doc in index.html, resetZoomWindow()), measured on the RTL:
//   gen_ramp.v  : interval between ramp floor triggers (trigger_low) and between ceil triggers (trigger_hig),
//                 triangle and sawtooth (both directions), several low/high/step values.
//                 Expected: sawtooth (hig-low+1)*(step+1), triangle 2*(hig-low)*(step+1) clock cycles.
//   gen_mod_h.v : interval between harmonic_trig pulses. Expected 2520*(hp+1) clock cycles.
// Run with test/ramp_mod_period_sim.sh (Vivado 2020.1 xsim). Prints "TB RESULT: PASS" if all match.
module ramp_mod_period_tb;
    reg clk = 0, rst = 1;
    always #4 clk = ~clk;

    reg         [31:0] step;
    reg  signed [13:0] low, hig;
    reg                saw, dir, enable, rreset;
    wire               t_low, t_hig;
    wire signed [13:0] outA, outB;

    gen_ramp #(.R(14)) dut_ramp (
        .clk(clk), .rst(rst),
        .ramp_step(step), .ramp_low_lim(low), .ramp_hig_lim(hig), .ramp_B_factor(14'd0),
        .ramp_reset(rreset), .ramp_enable(enable), .ramp_direction(dir), .ramp_sawtooth(saw),
        .relock_enable(1'b0), .out_of_lock(1'b0), .relock_reset(1'b0),
        .trigger_low(t_low), .trigger_hig(t_hig), .ramp_direction_out(), .outA(outA), .outB(outB)
    );

    reg  [13:0] hp;
    wire        h_trig;
    gen_mod_h dut_mod (
        .clk(clk), .rst(rst), .phase(12'd0), .phase_sq(32'd0), .hp(hp),
        .sin_ref(), .cos_ref(), .cos_1f(), .cos_2f(), .cos_3f(), .cntu_w(), .harmonic_trig(h_trig)
    );

    integer cyc = 0;
    always @(posedge clk) cyc <= cyc + 1;

    integer errors = 0, checks = 0;

    // interval between the n-th and (n+1)-th pulse of sig (after skipping the first ones)
    task measure_ramp(input integer exp, input [8*16-1:0] name);
        integer k, t0, tl, th, pl, ph, nl, nh;
        begin
            nl = 0; nh = 0; pl = -1; ph = -1; tl = -1; th = -1;
            // wait 3 full periods, keep the last interval of each trigger
            for(k = 0; k < 4 * exp + 100; k = k + 1) begin
                @(posedge clk); #1;
                if(t_low) begin if(tl >= 0) pl = cyc - tl; tl = cyc; nl = nl + 1; end
                if(t_hig) begin if(th >= 0) ph = cyc - th; th = cyc; nh = nh + 1; end
            end
            checks = checks + 1;
            if(pl != exp || ph != exp) begin
                errors = errors + 1;
                $display("FAIL %0s low=%0d hig=%0d step=%0d: floor period %0d, ceil period %0d, expected %0d",
                         name, low, hig, step, pl, ph, exp);
            end else
                $display("ok   %0s low=%0d hig=%0d step=%0d: floor/ceil period %0d cycles", name, low, hig, step, pl);
        end
    endtask

    task run_ramp(input integer l, input integer h, input integer s, input sw, input d);
        integer exp;
        begin
            rreset = 1; low = l; hig = h; step = s; saw = sw; dir = d; enable = 1;
            repeat(5) @(posedge clk);
            rreset = 0;
            exp = sw ? (h - l + 1) * (s + 1) : 2 * (h - l) * (s + 1);
            measure_ramp(exp, sw ? (d ? "sawtooth up  " : "sawtooth down") : "triangle     ");
        end
    endtask

    task run_mod(input integer h);
        integer k, t, p, exp;
        begin
            hp = h; t = -1; p = -1;
            exp = 2520 * (h + 1);
            for(k = 0; k < 3 * exp + 10; k = k + 1) begin
                @(posedge clk); #1;
                if(h_trig) begin if(t >= 0) p = cyc - t; t = cyc; end
            end
            checks = checks + 1;
            if(p != exp) begin
                errors = errors + 1;
                $display("FAIL harmonic hp=%0d: period %0d, expected %0d", h, p, exp);
            end else
                $display("ok   harmonic hp=%0d: period %0d cycles", h, p);
        end
    endtask

    initial begin
        step = 0; low = 0; hig = 10; saw = 0; dir = 0; enable = 0; rreset = 1; hp = 0;
        repeat(10) @(posedge clk);
        rst = 0;
        run_ramp(-100, 100, 0, 0, 0);
        run_ramp(-100, 100, 3, 0, 0);
        run_ramp(  -7,  50, 9, 0, 1);
        run_ramp(-100, 100, 0, 1, 0);
        run_ramp(-100, 100, 3, 1, 0);
        run_ramp(-100, 100, 3, 1, 1);
        run_ramp(  -7,  50, 9, 1, 1);
        run_mod(0);
        run_mod(1);
        run_mod(4);
        $display("TB RESULT: %0s (%0d checks, %0d errors)", errors ? "FAIL" : "PASS", checks, errors);
        $finish;
    end
endmodule
