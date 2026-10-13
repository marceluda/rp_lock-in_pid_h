# Pipeline registers of v2.3.19 (FPGA timing) — added latencies

Up to v2.3.18 the FPGA design did not meet timing at 125 MHz (`adc_clk`, 8 ns): WNS −8.954 ns,
TNS −9565 ns, 5101 failing endpoints (Vivado 2020.1, v2.3.17 image). The worst paths were long
combinational chains of the loop that started at a register and went through several blocks
without any register in between:

- lock-in: ROM of the generator (block RAM without output register) + sign change → product →
  first LPF (or its bypass) → second LPF (or its bypass) → `<<< sg_amp` → two saturations → `Xo..F3o`
  → PID input / scope muxes / signal of `lock_ctrl` / `error` mux;
- PID: `kp_reg + int_shr + kd_reg` (64 bits) → saturation → `ctrl_A/B` (+ ramp, saturation) → out mux
  → + modulation → saturation → DAC registers and scope muxes;
- modulation: ROM → sign change → `mod_out × cos_ref` → + out mux → saturation → DAC.

The user allowed adding latency to fix it (2026-10-12). v2.3.19 adds registers in those chains and
rewrites some blocks with fewer logic levels (same values). **The behaviour is the one of v2.3.18
except for the latencies below** (checked bit by bit in simulation, `test/lock_latency_sim.sh`).

## 1. Registers added (latency)

| Where | File | Added latency | What it affects |
|---|---|---|---|
| Outputs of the generator (`sin_ref`, `cos_ref`, `cos_1f`, `cos_2f`, `cos_3f`) and `harmonic_trig` | `lock/gen_mod_h.v` | +1 clock (8 ns), all of them | the whole generator comes 1 clock later: modulation, references of the lock-in, scope signals 12-16, trigger "harmonic mod." (same waveforms, same phases between them) |
| Output of the first LPF stage (`LP_filter3 .OREG(1)`, filtered value or bypass) | `lock/LP_filter3.v`, `lock.v` | +1 clock | `X_28..F3_28` (bus) and `Xo..F3o` |
| `Xo`, `Yo`, `F1o`, `F2o`, `F3o` (after the gain and saturation) | `lock.v` | +1 clock | `Xo..F3o` (total +2 with the LPF register) |
| PID output (`dat_o = dat_o_mem`) and the enable that gates it (`pidA/B_enable_d`) | `lock/lock_pid_block.v`, `lock.v` | +1 clock | `pidA_out`, `pidB_out` (and their copies), `ctrl_A`, `ctrl_B` (PID part) |
| Outputs to the DACs: the two terms of `out1/out2` (out mux and modulation) | `lock.v` | +1 clock | `out1`, `out2` (DACs, scope signals 23/24, bus 0xDC/0xE0) for everything that goes out |

## 2. Latency of each signal with respect to v2.3.18

"+n" = the signal is the one of v2.3.18 delayed n clocks (n × 8 ns), for the same input.

| Signal | From | Added | ns |
|---|---|---|---|
| `sin_ref`, `cos_ref`, `cos_1f`, `cos_2f`, `cos_3f`, `harmonic_trig` | generator (reset / phase / hp) | +1 | 8 |
| `Xo`, `Yo`, `F1o`, `F2o`, `F3o` | product `signal_i × reference` | +2 | 16 |
| `X_28`, `Y_28`, `F1_28`..`F3_28` (bus 0xEC..0xFC) | product | +1 | 8 |
| `error` | its source (`Xo..F3o`: +2 as above; `in1`, `in1-in2`: 0) | 0 | 0 |
| `pidA_out`, `pidB_out`, `pidX_out` (scope, bus) | PID input `pidX_in` | +1 | 8 |
| `ctrl_A`, `ctrl_B` | PID input: +1; ramp and jump: 0 | +1 / 0 | 8 / 0 |
| `out1`, `out2` (DAC) | whatever is selected (out mux + modulation) | +1 | 8 |
| Lock trigger (`lock_ctrl`, level) | the signal for trigger: `Xo..F3o` +2, PID out +1, `in1` 0 | as its signal | |
| Scope channels | as the selected signal (the scope mux is the same) | | |

End to end, for an input step on `in1` (`test/lock_latency_sim.sh`, first clock in which the output moves):

| Path | v2.3.18 | v2.3.19 | Added |
|---|---|---|---|
| `in1` → `Xo` (LPF bypassed) | 1 clock | 3 clocks | +16 ns |
| `in1` → `pidA_out` (PID A on `in1`, kp only) | 2 | 3 | +8 ns |
| `in1` → `Xo` → `pidA_out` | 3 | 6 | +24 ns |
| `in1` → `Xo` → PID A → `ctrl_A` → `out1` (the LOCK MODE loop) | 3 | 7 | +32 ns |
| `in1` → PID A → `ctrl_A` → `out1` | 2 | 4 | +16 ns |
| `in1` → `out1` (`out1_sw` = in1) | 0 | 1 | +8 ns |

Effects to keep in mind:

- **Loop delay.** The LOCK MODE loop (`in1` → Y → error → PID A → `out1`) has 32 ns more delay. At the
  frequencies of the PID loop (the lock-in LPF of LOCK MODE is 262 µs, 2nd order) the extra phase is
  negligible (0.1° at 10 kHz).
- **Phase of the lock-in in a loop through the DAC.** The references and the modulation come 1 clock later
  (no change between them), but the output register adds 1 more clock to the modulation that goes out
  through `out1`: a signal that comes back to `in1` (modulation → system → `in1`) is 8 ns later with
  respect to the reference, i.e. the measured phase changes by −360° · f · 8 ns: **−0.143° at 49.6 kHz**
  (`gen_mod_hp` 0), which is exactly one step of `gen_mod_phase` (1/2520 of the period at hp 0), and
  proportionally less at lower frequencies. No compensation is applied (C or page): the phase is a
  parameter of the user and the difference is below the resolution that matters for the lock. A config
  that needs the old phase exactly can add 1 to `gen_mod_phase` at hp 0.
- **Scope.** All the channels go through the same scope mux: a trace of `Xo` is 2 clocks later than
  before with respect to `in1` and to the trigger, `out1` 1 clock. Not visible at the usual time scales
  (µs to s). *Choose from graph* takes the time from the trace, i.e. with the same latency as the signal
  that triggers the lock: no change.
- **Lock control.** The Time trigger is counted from the scan floor, as before (no change). The Level
  trigger fires 2 clocks later when the signal for trigger is a lock-in output, 1 clock later on a PID output.
- **Bus reads** of `X_28..F3_28`: 1 clock later (they are read from the frozen copies anyway).

## 3. Blocks rewritten without latency (same values)

| Block | Change | Exceptions |
|---|---|---|
| Gain + saturation of `Xo..F3o` (`<<< sg_amp`, `satprotect2(53→38)` or `(43→28)`, then `[37:21]` / `[27:11]` and `satprotect2(17→14)`) | `lock/shift_sat14.v`: one test of 19 bits instead of two saturations in series (derivation in the header of the file) | none (checked with 800000 random vectors and all the shifts) |
| Second LPF stage (`LP_filter3 .DREG(1)`) | `sum_div` (the shift of the accumulator by `tau`) is a register loaded with the shift of the value being loaded in the accumulator: the output in filter mode starts at a register | a change of `lpf_F*` reaches that shift 1 clock later (1 clock after a write of the register) |
| `sat14` (saturation with a limit set at run time) | `|(in >> lim)` → `|(in & ({RES{1}} << lim))`: no barrel shifter in the data path | none (checked with 400000 random vectors, `lim` 0..80) |
| Integrator of the PID | the saturation is written out in `lock_pid_block.v` (the one of `sat14`) and the shift by ISR of `int_shr_reg` is applied to each of the three possible values in parallel | none |

Not a plain delay: the derivative of the PID with `DSR` > 0 samples its input every 2^n clocks with a
counter that runs from the reset; with a delayed input (e.g. PID on `Xo`) it takes other samples. Same
behaviour, other sampling phase.

## 4. Verification (`test/lock_latency_sim.sh`)

xsim (Vivado 2020.1): the `lock.v` of the working tree (N) and the one of v2.3.18 (O, `git show 5e3e748`,
modules renamed `o_*`) side by side, same bus writes. In the scenarios with the generator involved N
gets `in1`/`in2` 1 clock later (what happens in a real loop through the DAC), so every signal of N must be
the one of O delayed by 1 + the latency of the table; with `in1` not delayed only the paths that do not
mix `in1` with the generator are compared. 412 checks, all bit exact:

- U1 / U2: `sat14` and `shift_sat14` against the old blocks (random vectors);
- S1 LOCK MODE-like (LPF 262 µs 2nd order, `sg_amp0` 5, error = Yo, PID A on error kp −250 ki −20,
  PID B on F1o, one LPF per order on F1..F3), 150000 clocks;
- S2 both LPF bypassed, `sg_amp` 0..30 (saturation and the wrap of the shift), PIDs on Xo/F3o;
- S3 PIDs on `in1`/`in2`, PSR/ISR/DSR/SAT/kd/ki/set point swept (integrator saturation);
- S4 modulation on `out1`/`out2` (with and without delaying `in1`);
- S5 Level trigger of `lock_ctrl` on `Xo`;
- S6 step responses (table of §2).

`test/lock_bus_read_sim.sh` (bus reads) and `test/lock_ctrl_sim.sh` (lock control) pass unchanged.

## 5. Timing (Vivado 2020.1, post-route)

| | v2.3.18 (image of v2.3.17) | v2.3.19 |
|---|---|---|
| WNS | −8.954 ns | −1.099 ns |
| TNS | −9564.6 ns | −207.5 ns |
| Failing endpoints | 5101 | 774 |
| adc_clk → dac_clk_1x | −8.789 ns (DAC) | +1.123 ns |
| Slice LUTs / registers | 13193 / 9975 | 12842 / 10546 |

Worst path per group (setup slack, ns):

| Group | v2.3.18 | v2.3.19 |
|---|---|---|
| scope muxes (`i_muxer5_scope*`) | −8.954 | −0.292 |
| DAC registers | −8.789 | > 0 |
| `adc_dat` (digital loop / scope input) | −8.380 | −1.099 (scope configuration → decimator input, outside the lock module) |
| bus copies `*_rd` | −8.645 | −0.202 |
| PID A / PID B (inputs and internal) | −7.502 / −7.958 | −0.818 / −0.783 |
| `lock_ctrl` (signal for trigger) | −5.561 | −0.012 |
| rest of the lock module | −4.272 | −0.517 |
| LPF | −2.908 | −0.728 |
| ramp | −2.987 | −0.198 |
| generator | −2.366 | > 0 |

What still fails (≈ −1.1 to −0.2 ns): the recursive loops of the LPF (accumulator of 64 bits with
saturation: they cannot be pipelined without changing the filter) and of the PID integrator, the input
path `in1` → PID mux → set point subtraction → multiplier, the relock comparison on `in1`, and paths of
the oscilloscope and the bus decoder outside the lock-in.
