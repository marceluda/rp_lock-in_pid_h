# The App: instruments and specifications

`lock_in+pid_harmonic` ("Harmonic Lock-in+PID") **v2.3.24** for the Red Pitaya STEMlab 125-14,
Ecosystem 2.0 (tested on RedPitaya_OS 2.04-35). Branch `master`.

This page describes what the App contains and its technical data. How to use it from the web page is in
[Usage.md](Usage.md); how the parts are connected in [Structure.md](Structure.md); the registers in
[FPGA.md](FPGA.md).

- [The instruments](#the-instruments)
- [General data](#general-data)
- [Oscilloscope](#oscilloscope)
- [Inputs and outputs](#inputs-and-outputs)
- [Modulation generator](#modulation-generator)
- [Harmonic lock-in amplifier](#harmonic-lock-in-amplifier)
- [Ramp generator (scan)](#ramp-generator-scan)
- [Error signal and PIDs](#error-signal-and-pids)
- [Lock control (auto-lock)](#lock-control-auto-lock)
- [Re-lock and step response](#re-lock-and-step-response)
- [Monitor](#monitor)
- [Streaming](#streaming)
- [Remote control](#remote-control)

## The instruments

Like the [Lock-in+PID](https://marceluda.github.io/rp_lock-in_pid/TheApp/instruments/instruments_01_intro/)
App it comes from, this App is a set of "instruments" built inside the FPGA. They are not isolated
blocks: they are a logical division of one circuit (`lock.v`), whose signals can be routed to each other
with selectors, so that a measurement or a feedback loop is configured instead of wired.

| Instrument | What it does | Main registers |
|---|---|---|
| **Oscilloscope** | Two channels, any of 25 internal signals, 16384 samples, time spans from 131 µs to 68.7 s, external trigger from internal events | scope block 0x40100000, `oscA_sw`, `oscB_sw`, `trig_sw` |
| **Inputs / outputs** | Routing of 16 signals to the fast outputs OUT1/OUT2, with optional modulation added | `out1_sw`, `out2_sw`, `mod_out1`, `mod_out2` |
| **Modulation generator** | Harmonic local oscillator: `sin_ref`, `cos_ref` and `cos_1f`, `cos_2f`, `cos_3f` with adjustable phase, 3 Hz – 49.6 kHz | `gen_mod_hp`, `gen_mod_phase` |
| **Harmonic lock-in** | Demodulation of one input at 1f (X, Y and F1 at an arbitrary phase), 2f (F2) and 3f (F3), with 1st/2nd order low-pass filters and gains | `signal_sw`, `lpf_F*`, `sg_amp*` |
| **Ramp generator** | Triangle or sawtooth scan on two outputs with a fixed ratio (A and B) | `ramp_*` |
| **Two PIDs** | PID A and PID B, wide range of gains and time constants, integrator saturation, freeze and reset | `pidA_*`, `pidB_*`, `error_sw`, `error_offset` |
| **Lock control** | Automatic transition from scan (open loop) to lock (closed loop) at a time, a level or immediately, executed by the FPGA in one clock | `lock_control`, `lock_status`, `lock_trig_*` |
| **Re-lock / step response** | Out-of-lock detection; a step added to the control signals to measure the loop response | `rl_*`, `sf_*` |
| **Monitor** | Mean and standard deviation of the error over ~1 s | `error_mean`, `error_std` |
| **Streaming** | Continuous transfer of the two scope channels to a computer over TCP | `stream_*` |
| **Remote control** | HTTP API to read and write all the registers, make scope acquisitions and run the lock (Python client `control_finn.py`) | `/lock`, `/osc`, `/data` |

The two control signals of the App are:

```
ctrl_A = PID A out + Ramp A (+ jump A)     → usually sent to OUT1
ctrl_B = PID B out + Ramp B (+ jump B)     → usually sent to OUT2
```

## General data

| Item | Value | Source |
|---|---|---|
| Board | STEMlab 125-14 (Zynq 7010, model Z10) | `fpga/README.md` |
| Ecosystem | 2.0 (RedPitaya_OS 2.04-35 tested); FPGA loaded by `fpga.sh` with `fpgautil` | `fpga.sh`, test reports |
| FPGA clock | 125 MHz (8 ns) | `src/fpga.c` l. 50, top |
| ADC / DAC | 14 bit, 125 MS/s; signals are 14-bit signed, 8192 counts = 1 V | `lock.v`, `index.html` |
| FPGA timing | almost closes since v2.3.19 (WNS −1.099 ns, v2.3.20 −0.888 ns; the image of v2.3.23, with the new `lock_ctrl.v`, **a confirmar**; was −8.954 ns: pipeline registers in the lock-in, PIDs, generator and outputs, [`lock_latency.md`](../lock_in+pid_harmonic/doc/lock_latency.md)); works in practice. Bus reads of the lock module are exact since v2.3.17 ([FPGA.md](FPGA.md#lock-module-0x40600000)) | CHANGELOG v2.3.10, v2.3.17, `devAgent.md` |

## Oscilloscope

The Red Pitaya 2.0 scope, fed by two internal signals chosen with `oscA_sw`/`oscB_sw` (not directly by
the ADCs). See [FPGA.md](FPGA.md#oscilloscope-0x40100000).

| Item | Value |
|---|---|
| Channels | 2 (any of: 0, in1, in2, error, ctrl_A, ctrl_B, Ramp A/B, pidA/B_in, PID A/B out, sin_ref, cos_ref, cos_1f/2f/3f, Xo, Yo, F1o, F2o, F3o, signal_i, out1, out2) |
| Memory | 16384 samples per channel; the web page gets 1024 points (`SIGNAL_LENGTH`, `src/main.h`) |
| Decimations (time range) | 1 (131 µs), 8 (1.05 ms), 64 (8.4 ms), 128 (16.8 ms), 256 (33.6 ms), 512 (67.1 ms), 1024 (134 ms), 8192 (1.07 s), 65536 (8.6 s), 524288 (68.7 s) — `src/fpga.c` l. 541-577; 20-bit decimation in the FPGA of this App |
| Trigger sources | Channel 1, Channel 2, External; modes Auto, Normal, Single; edge rising/falling |
| External trigger | Any of: pin DIO0_P, scan floor, scan ceil, start of the modulation period, out of lock, jump (step response), lock event ("Lock control trig") — `trig_sw` |
| Other | Averaging at decimation, anti-aliasing (equalization) filter bypass per channel, Raw mode (values in counts), save data as Python / Matlab / CSV |
| Web page tools | Reset zoom to the period of the trigger source (v2.3.21; 0.98 × T for T ≥ 1.5 s, v2.3.23), mouse wheel zoom on both axes / time only (SHIFT) / Y only (ALT) (v2.3.22), OscA\|OscB presets (v2.3.24): [Usage.md](Usage.md#toolbar) |
| Slow windows (≥ 1.5 s) | read while the FPGA writes them; only samples of the current acquisition are shown, never an older lap of the memory (v2.3.23, `src/worker.c`): [Usage.md](Usage.md#slow-scans) |

The time span of the 68.7 s range was verified on the board (v2.3.10, `reportes/lock-in_pid_h.md`).

## Inputs and outputs

| Item | Value |
|---|---|
| Fast inputs IN1, IN2 | 14 bit; ±1 V (LV jumper) or ±20 V (HV); the gain setting of the UI only changes the scale of the display |
| Fast outputs OUT1, OUT2 | 14 bit, ±1 V, 8192 counts = 1 V; any of 0, in1, in2, in1−in2, error, cos_1f, cos_2f, cos_3f, cos_ref, sin_ref, PID A out, PID B out, ctrl_A, ctrl_B, aux_A, aux_B |
| Modulation added to the outputs | OUT1 + `cos_ref · mod_out1 / 2^13`, OUT2 + `sin_ref · mod_out2 / 2^13`, saturated to 14 bits; off with a negative `mod_out*` (`lock.v` l. 428-448) |
| `in1 − in2` | difference saturated to 14 bits |
| `aux_A`, `aux_B` | two constants (−8192..8191) usable as signals |
| Slow outputs AO0-AO3 | **not driven by the lock module in this version** (the UI shows four selectors that have no effect). See [FPGA.md](FPGA.md#other-blocks) |
| Digital I/O | DIO0_P: trigger input; DIO6_N: ramp direction output; DIO7_N: digital modulation (always 0) |

## Modulation generator

`lock/gen_mod_h.v`. A table of 630 points (one quarter of period) is read forwards and backwards to make
a period of **2520 points**; each point lasts `gen_mod_hp + 1` clock ticks.

| Item | Value |
|---|---|
| Frequency | f = 125 MHz / (2520 · (`gen_mod_hp` + 1)) |
| Range | `gen_mod_hp` = 0 → **49.603 kHz**; 16383 → **3.03 Hz** |
| Phase | `gen_mod_phase` 0..2519 → 0..359.86°, step 360°/2520 = 0.143°; applies to `cos_1f`, `cos_2f`, `cos_3f` |
| Amplitude of the references | ±4094 counts (≈ ±0.5 V) — `data_*_ss.dat` |
| Signals | `cos_ref` (phase 0), `sin_ref` (quadrature), `cos_1f`, `cos_2f` (2f), `cos_3f` (3f) |
| Modulation on an output | amplitude ≈ `mod_out / 2` counts = `mod_out / 16384` V; max `mod_out` = 8191 → ≈ 0.5 V |

Example: `gen_mod_hp = 255` → 193.8 Hz (`example_usage.py`). The web UI shows the resulting period and
frequency below the field, and the phase in degrees and radians.

## Harmonic lock-in amplifier

`lock.v` l. 725-908, `lock/LP_filter3.v`.

```
signal_i ─┬─ × cos_ref ─ LPF(F0) ─ X_28 ─ ×2^sg_amp0 ─ sat ─ Xo
          ├─ × sin_ref ─ LPF(F0) ─ Y_28 ─ ×2^sg_amp0 ─ sat ─ Yo
          ├─ × cos_1f  ─ LPF(F1) ─ F1_28 ─ ×2^sg_amp1 ─ sat ─ F1o
          ├─ × cos_2f  ─ LPF(F2) ─ F2_28 ─ ×2^sg_amp2 ─ sat ─ F2o
          └─ × cos_3f  ─ LPF(F3) ─ F3_28 ─ ×2^sg_amp3 ─ sat ─ F3o
```

| Item | Value |
|---|---|
| Input `signal_i` | in1, in2, in1−in2, cos_ref, sin_ref, cos_1f, aux_A, Ramp A |
| Outputs | `Xo`, `Yo` (1f, phase 0 and 90°), `F1o` (1f at `gen_mod_phase`), `F2o` (2f), `F3o` (3f); 14-bit, saturated |
| Scale | with gain ×1 the outputs read the **amplitude** (in counts) of the component of the input in phase with each reference: an input `A·cos_ref/4094` gives `Xo ≈ A`, `Yo ≈ 0`; an input in phase with `sin_ref` gives `Yo ≈ A` (φ = +90°). Times 2^`sg_amp`. Derived from the RTL (reference ±4094 ≈ 2^12, products shifted 21 bits) and consistent with the loopback test OUT1 → IN1: `cos_ref` → X = 461 mV, φ = 1.6°; `sin_ref` → Y = R = 461 mV, φ = 91.6° (`reportes/lock-in_pid_h.md`) |
| Gains | `sg_amp0` ×1 .. ×512k (UI; register up to 2^31); `sg_amp1..3` ×1 .. ×512 (UI; register up to 2^15) |
| Low-pass filters | 4 independent: X&Y share `lpf_F0`, then F1, F2, F3. Order 0 (off), 1 or 2 (cascade of identical 1st-order stages) |
| Latency | v2.3.19: outputs 2 clocks (16 ns) later than in v2.3.18, the generator 1 clock later, the PID outputs and `out1`/`out2` 1 clock each ([`lock_latency.md`](../lock_in+pid_harmonic/doc/lock_latency.md)) |
| Time constants | τ = 8 ns · 2^(14+n), n = 0..15 |
| R and φ | computed in the web page from X and Y: R = √(X² + Y²), φ = atan2(Y, X) |
| Registers with more resolution | `X_28`, `Y_28`, `F1_28`..`F3_28` (28 bit, before the gain): `X_28 ≈ A·cos φ · 2^11` |

Low-pass filter table (`LP_filter3.v`, also the labels of the UI):

| n | τ | f = 1/(2πτ) | n | τ | f = 1/(2πτ) |
|---|---|---|---|---|---|
| 0 | 131 µs | 1.21 kHz | 8 | 33.6 ms | 4.74 Hz |
| 1 | 262 µs | 607 Hz | 9 | 67.1 ms | 2.37 Hz |
| 2 | 524 µs | 304 Hz | 10 | 134 ms | 1.19 Hz |
| 3 | 1.05 ms | 152 Hz | 11 | 268 ms | 593 mHz |
| 4 | 2.10 ms | 75.9 Hz | 12 | 537 ms | 296 mHz |
| 5 | 4.19 ms | 37.9 Hz | 13 | 1.07 s | 148 mHz |
| 6 | 8.39 ms | 19.0 Hz | 14 | 2.15 s | 74.1 mHz |
| 7 | 16.8 ms | 9.49 Hz | 15 | 4.29 s | 37.1 mHz |

To reject the modulation the cut-off frequency has to be well below the modulation frequency (2f is the
main component of the product). Example: modulation at 49.6 kHz and n = 1 (607 Hz), order 2 (the test
configuration `lock_mode`).

## Ramp generator (scan)

`lock/gen_ramp.v`.

| Item | Value |
|---|---|
| Shape | triangle (`ramp_sawtooth` = 0) or sawtooth (1); starting direction / direction of the sawtooth with `ramp_direction` |
| Limits | `ramp_low_lim` .. `ramp_hig_lim`, −8192..8191 (±1 V); default ±5000 (±610 mV) |
| Step | one count every `ramp_step + 1` ticks |
| Period | T = (hig − low) · (`ramp_step` + 1) · 8 ns · (2 − sawtooth); e.g. ±5000, `ramp_step` = 400 triangle → 64.16 ms (test configurations, seen on the board, [panel](Usage.md#ramp-controller)); `ramp_step` = 187499 triangle → 30.00 s ([slow scans](Usage.md#slow-scans)) |
| Second output | `ramp_B = ramp_A · ramp_B_factor / 4096` (factor −4096..4096 in the UI, i.e. −1..1) |
| Triggers | "Scan floor" (low limit reached) and "Scan ceil" (high limit), for the scope and for the time trigger of the lock |
| Enable | runs while `ramp_enable` (Ramp panel, "Scan enable" checkbox) **and** the ramp enable of the lock control ("Scan enable" button) are on; `ramp_reset` holds it at 0 |
| Digital output | ramp direction on DIO6_N |

## Error signal and PIDs

`lock.v` l. 555-580 and 913-1007, `lock/lock_pid_block.v`.

The **error** is one of 0, Xo, Yo, F1o, F2o, F3o, in1, in1−in2, minus `error_offset`. Each PID can take
the error or one of 15 other signals (`pidX_sw`).

PID equation, with e = `sp − in` (the sign of the gains selects the sign of the feedback):

```
out = kp·e / 2^P  +  Σ(ki·e) / 2^I  +  kd·(slope of e) / 2^6
```

| Item | Value | Notes |
|---|---|---|
| `kp`, `ki`, `kd`, `sp` | −8192..8191 | 14-bit signed |
| Proportional divider P (PSR) | /1, /8, /64, /1024, /4096 | default /1024 (`kp` = 1024 → gain 1) |
| Integrator (ISR) | 2^I, I = 0,3,6,10,13,16,20,23,26,30 → UI labels 8 ns, 64 ns, 512 ns, 8 us, 65 us, 524 us, 8 ms, 67 ms, 537 ms, 9 s (the "65 us" label said "6 us" up to v2.3.14) | characteristic time τ_i = 8 ns · 2^I / |ki|; default I = 26 (537 ms) |
| Derivative (DSR) | slope over averages of 2^D samples, D = 0,3,6,10,13,16 → UI 7.5 ns .. 491.5 µs | τ_d = 7.5 ns · 2^D · |kd| (UI formula) |
| Integrator saturation (SAT) | integral term limited to ±2^SAT counts: ±122 µV (0) .. ±1 V (13) | default 13 |
| Output | sum saturated to 14 bits (±1 V) | |
| Controls | integrator reset, freeze output, freeze integrator (`pidX_ctrl`) | also frozen during a step (`sf_config`) |
| Enable | the output is forced to 0 and the integrator reset while the PID is disabled by the lock control | `lock.v` l. 962 |

Example (test configuration `lock_mode`): PID A, kp = −250 with /1024 → −0.244; ki = −20 with 537 ms →
τ_i = 26.8 ms (seen in the [PID panel](Usage.md#pids-modules)).

## Lock control (auto-lock)

The lock sequence runs in the FPGA (`lock/lock_ctrl.v`, since v2.3.13). Full design:
[`lock_control.md`](../lock_in+pid_harmonic/doc/lock_control.md).

| Item | Value |
|---|---|
| States | OFF (IDLE) → ARMED → LOCKED |
| In IDLE / ARMED | ramp, PID A, PID B follow the manual enables ("Scan enable", "PID A enable", "PID B enable") |
| In LOCKED | they follow the "config" enables (usually: ramp off, PID A on) |
| Requests | Lock Now (immediate), Trigger Lock (arm, lock on the trigger) |
| Triggers | **Time**: `lock_trig_time` ticks (8 ns) after the scan floor, 0..2³²−1 (up to 34.36 s; 32-bit counter since v2.3.15, it was 17.18 s; since v2.3.23 the counter saturates and the time trigger only fires after a floor of a running ramp, [FPGA.md](FPGA.md#lock-control-auto-lock)); **Level**: a signal crosses `lock_trig_val` upwards or downwards; **Level+time**: level crossing after the time |
| Latency | the change happens in the same clock tick as the trigger (8 ns); since v2.3.19 a lock-in output used as signal for trigger is itself 16 ns later than before ([`lock_latency.md`](../lock_in+pid_harmonic/doc/lock_latency.md)) |
| Status | `lock_status`: armed, locked, effective enables, count of locks |
| Capture | the lock event is a scope trigger source ("Lock control trig"); the web page uses it to capture the closing of the loop ([`lock_capture.md`](../lock_in+pid_harmonic/doc/lock_capture.md)) |

Measured on the board against a simulated peak (`dummy_simulator` on a second Red Pitaya, LOCK MODE
procedure of `test_files/lock_test.md`, v2.3.11 to v2.3.17; `reportes/lock-in_pid_h_lock_test/`):

| Metric | Value |
|---|---|
| Time from the request (POST) to ARMED | 17 ms (the controller waits for the scope to be armed) |
| ARMED → LOCKED | 5-47 ms (first sweep after arming, time trigger at 16.58 ms; 16.9 ms in v2.3.14, 26 / 47 ms in v2.3.17) |
| Captures of the lock in the scope with Capture Lock | 16/16 |
| Signal at the lock point | IN1 = 1.01–1.03 × the peak |
| Error while locked | mean ≈ 0, std ≈ 27 counts ≈ 3.3 mV with kp = −250 (v2.3.24, [Monitor](Usage.md#lock-control)); ≈ 7–8 mV with the kp = −500 used up to 2026-10-12 |
| Longest lock observed | 4 h 10 min without losses (level trigger) |

## Re-lock and step response

- **Re-lock** (`rl_*`): "out of lock" = `|error| > rl_error_threshold` and/or `signal < rl_signal_threshold`
  (signal: in1, in2, in1−in2, aux_A, aux_B), debounced (`lock/lock_debounce.v`). It is a scope trigger
  source, and with re-lock enabled the ramp generator switches to a search around the current point
  (`lock/gen_ramp_relock.v`). `rl_state` is not implemented (reads 0). The behaviour of the search has not
  been tested on the 2.0 version: **a confirmar**.
- **Step response** (`sf_*`): "Start Step Responce" adds `sf_jumpA`/`sf_jumpB` to `ctrl_A`/`ctrl_B`
  2¹⁶ ticks (524 µs) after the start (`jump_control`, N = 16), and can freeze the outputs or integrators
  of the PIDs during the step. "Jump trigger" is a scope trigger source. Not tested on 2.0: **a confirmar**.

## Monitor

`error_mean` and `error_std` are computed in the FPGA over 2²⁷ ticks (1.074 s) and shown in the Monitor
panel in counts (`src/lock.c` l. 440-442).

## Streaming

`c/streaming` (started by the "Prepare Streaming" button) waits for `stream_cmd = 1` and then runs
`c/stream_tcp_osc_cmd`, which reads the scope memory continuously and sends both channels to
`stream_ip:stream_port` over TCP. A receiver is in `resources/streaming/` (instructions in
`resources/README.md`).

| Rate (`stream_rate` = decimation) | Result on the board (v2.3.10) |
|---|---|
| 64 (1.95 MS/s) | not sustainable: 1.63 MS/s, ~17 % of the samples lost (counted) |
| 128 (0.98 MS/s) | 976.5 kS/s, 0 duplicates in 311 M samples (318 s) |
| 256 .. 65536 | sustainable |

## Remote control

- **HTTP** (recommended): `http://rp-XXXXXX.local/lock_in+pid_harmonic/lock` and `.../osc` read and write
  the registers of the lock module and of the scope, and read the scope memory; `POST /data` stops or restarts
  the scope of the C controller. Python client `resources/remote_control/http_version/control_finn.py`
  (v2.3.15-2.3.17: triggered acquisitions on the 2.0 scope, PID / ramp / lock-in / lock helpers, host name
  resolved once, minimal `POST /data`). See [Remote.md](Remote.md).
- **On the board**: `c/lock`, `c/osc` and the Python scripts of `py/` (e.g. `lock_from_registers.py`).
- **SSH** version (`resources/remote_control/shh_version`): deprecated, kept for specific cases.
