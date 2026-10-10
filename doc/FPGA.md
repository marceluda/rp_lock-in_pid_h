# FPGA register map

Register map of the FPGA design of `lock_in+pid_harmonic` **v2.3.14** (branch `devel2.0`, Vivado 2020.1,
RedPitaya-FPGA project `v0.94`, model Z10 / STEMlab 125-14).

All registers are 32-bit words on the AXI general purpose bus of the Zynq, accessed from Linux through
`/dev/mem` (the C controller, the `c/lock` and `c/osc` tools, `py/hugo.py`). Every block is acknowledged
on the bus; unused addresses read 0.

- [Memory map of the blocks](#memory-map-of-the-blocks)
- [Number formats](#number-formats)
- [Lock module (0x40600000)](#lock-module-0x40600000)
  - [Bit fields](#bit-fields)
  - [Selector values](#selector-values)
- [Oscilloscope (0x40100000)](#oscilloscope-0x40100000)
- [Other blocks](#other-blocks)
- [Register description files (`lock.txt`, `osc.txt`)](#register-description-files-locktxt-osctxt)
- [Differences found between the files and the RTL](#differences-found-between-the-files-and-the-rtl)

Related documents: [App.md](App.md) (what each instrument does, with ranges in physical units),
[Structure.md](Structure.md) (how the registers are connected inside the FPGA), [Remote.md](Remote.md)
(how to read and write them over HTTP), and the design notes of the lock control
[`lock_control.md`](../lock_in+pid_harmonic/doc/lock_control.md) and of the lock capture
[`lock_capture.md`](../lock_in+pid_harmonic/doc/lock_capture.md).

## Memory map of the blocks

Source: `lock_in+pid_harmonic/fpga/README.md` and `fpga/prj/v0.94/rtl/red_pitaya_top.sv` (`sys[0..7]`).

| Base address | Size used | Block | Notes |
|---|---|---|---|
| `0x40000000` | — | Housekeeping (`red_pitaya_hk`, 2.0 version) | ID, LEDs, expansion connector, CAN enable. Not used by the App. |
| `0x40100000` | `0x30000` | **Oscilloscope** (`rp_scope_com`, Red Pitaya 2.0 scope with changes of this App) | Inputs = lock `osc1`/`osc2`; external trigger = lock `trigger`. Sample buffers at `+0x10000` (ch A) and `+0x20000` (ch B), 16384 words each. |
| `0x40200000` | — | (ASG removed) | `sys_bus_stub_ok`: acknowledged, no error, reads 0 |
| `0x40300000` | — | (PID removed) | `sys_bus_stub_ok`: acknowledged, no error, reads 0 |
| `0x40400000` | — | AMS / XADC | The PDM registers `0x40400020..2C` are readable but have no effect: the slow outputs are driven by the lock module (`red_pitaya_top.sv` l. 416-428) |
| `0x40500000` | — | Daisy chain | Not used by the App |
| `0x40600000` | `0x18C` (99 words) | **Lock module** (`lock.v`) | This App |

## Number formats

- The Red Pitaya fast ADCs and DACs are 14-bit. Inside the lock module almost every signal is a **14-bit
  two's complement integer**: `-8192 .. 8191`, where **8192 counts = 1 V** at the fast analog outputs and
  at the inputs in LV (±1 V) jumper setting (`index.html` uses `value/8192` V everywhere).
- Signed registers are **sign-extended to 32 bits on read** (e.g. `{ {18{x[13]}}, x }`), so they read as
  normal `int32`. On write, only the low `N` bits are taken (`sys_wdata[N-1:0]`), so writing a negative
  `int32` sets the right two's complement value.
- Unsigned registers read with zero padding.
- Clock: 125 MHz (`adc_clk`, 8 ns per tick). All times below are in ticks of 8 ns.

## Lock module (0x40600000)

Sources: the bus decoder of `fpga/prj/v0.94/rtl/lock.v` (block `[FPGA MEMORY DOCK]`, l. 1004-1305: reset
values l. 1013-1079, writes l. 1081-1181, reads l. 1202-1301; v2.3.17), declarations l. 57-128, and
`lock_in+pid_harmonic/c/lock.txt`. Absolute address = `0x40600000 + offset`. Index = `offset / 4` (the
index used by `c/lock`, `py/hugo.py` and `lock.txt`).

Column legend: **RW** read/write, **R** read only (writes ignored). **Bits** = width of the FPGA register.
**s/u** = signed / unsigned. **Range** = range of meaningful values (from `lock.txt`, corrected where the
RTL says otherwise, see the notes). **Reset** = value after the FPGA is loaded (reset of `lock.v`).
"Frozen by `read_ctrl[0]`" means that the value read is a copy that stops updating while
`read_ctrl[0] = 1`, so that several registers can be read at the same instant.

Bus reads (v2.3.17): `sys_rdata` only changes while a read is requested (`sys_ren`) and then holds its
value. The PS side of the bus (`sys_bus_cdc`, clock `fclk[0]`) takes it some cycles after `sys_ack`,
asynchronously to `adc_clk`; up to v2.3.16 `sys_rdata` was reloaded on every cycle, and ~2-3 % of the reads
of a signal that changes on every cycle (`in1`, `oscA` showing `in1`) returned a mix of the bits of two
values (e.g. `0x0118c9c1`). The read-only signals that are wires (`in1`, `in2`, `out1`, `out2`, `oscA`,
`oscB`, `pidA_in`, `pidA_out`, `pidB_in`, `pidB_out`, `ramp_A`, `ramp_B`, `sin_ref`..`cos_3f`, `error_mean`,
`error_std`, `lock_status`) are read from registered copies (`<name>_rd`, not frozen by `read_ctrl[0]`), so
the read multiplexer only has registers at its inputs. The real-time logic does not use them. While a read is
requested (`sys_ren`, 2 clocks with the address already stable) the `_rd` copies and the `_reg` copies of
`read_ctrl[0]` hold their value (the value read is the one of the clock before the request), so every input of
`sys_rdata` is stable for 2 clocks: `prj/v0.94/sdc/red_pitaya.xdc` has a 2-cycle multicycle constraint to
`i_lock/sys_rdata_reg`. Same kind of fix as the one of the scope `sys_rdata` in v2.3.10. Test:
`test/lock_bus_read_sim.sh`.

### Scope, trigger and outputs

| Offset | Idx | Name | R/W | Bits | s/u | Range | Reset | Function |
|---|---|---|---|---|---|---|---|---|
| `0x000` | 0 | `oscA_sw` | RW | 5 | u | 0..24 | 1 (in1) | Signal sent to oscilloscope channel A (1). See [selector values](#oscilloscope-channels-osca_sw-oscb_sw). |
| `0x004` | 1 | `oscB_sw` | RW | 5 | u | 0..24 | 2 (in2) | Signal sent to oscilloscope channel B (2). |
| `0x008` | 2 | `osc_ctrl` | RW | 2 | u | 0..3 | 3 | `[0]` bypass the equalization ("anti-aliasing") filter of scope ch 1, `[1]` the same for ch 2. |
| `0x00C` | 3 | `trig_sw` | RW | 8 | u | 0..255 (mask) | 0 | Mask of signals that make the **external trigger** of the scope. See [`trig_sw` bits](#trig_sw-0x00c). |
| `0x010` | 4 | `out1_sw` | RW | 4 | u | 0..15 | 0 | Signal sent to fast output OUT1. See [selector values](#fast-outputs-out1_sw-out2_sw). |
| `0x014` | 5 | `out2_sw` | RW | 4 | u | 0..15 | 0 | Signal sent to fast output OUT2. |

### Lock control (auto-lock)

| Offset | Idx | Name | R/W | Bits | s/u | Range | Reset | Function |
|---|---|---|---|---|---|---|---|---|
| `0x018` | 6 | `lock_control` | RW | 11 | u | 0..2047 | 1148 (`0x47C`) | Command + configuration of the lock state machine. Never modified by the FPGA (v2.3.13). See [bit fields](#lock_control-0x018). |
| `0x01C` | 7 | `lock_status` | R | 16 | u | 0..65535 | — | State of the lock (v2.3.13, replaced `lock_feedback`). See [bit fields](#lock_status-0x01c). |
| `0x020` | 8 | `lock_trig_val` | RW | 14 | s | -8192..8191 | 0 | Threshold of the **level** trigger, compared with the signal selected by `lock_trig_sw`. |
| `0x024` | 9 | `lock_trig_time` | RW | 32 | u | 0..2³¹−1 (see note 1) | 0 | Delay of the **time** trigger, in ticks of 8 ns counted from the last scan floor (`ramp_floor_trig`). |
| `0x028` | 10 | `lock_trig_sw` | RW | 4 | u | 0..15 | 0 | Signal used by the level trigger. See [selector values](#lock-trigger-signal-lock_trig_sw). |
| `0x02C` | 11 | `rl_error_threshold` | RW | 13 | u | 0..8191 | 0 | Re-lock: out of lock when `|error| > rl_error_threshold`. |
| `0x030` | 12 | `rl_signal_sw` | RW | 3 | u | 0..7 | 0 | Re-lock: signal compared with `rl_signal_threshold` (0 in1, 1 in2, 2 in1−in2, 3 aux_A, 4 aux_B, 5..7 → 0). |
| `0x034` | 13 | `rl_signal_threshold` | RW | 14 | s | -8192..8191 | 0 | Re-lock: out of lock when `signal < rl_signal_threshold`. |
| `0x038` | 14 | `rl_config` | RW | 3 | u | 0..7 | 0 | Re-lock: `[0]` enable error threshold, `[1]` enable signal threshold, `[2]` relock reset. |
| `0x03C` | 15 | `rl_state` | R | 5 | u | — | — | **Always reads 0** (`lock.v` l. 135, `assign rl_state = 5'b0`). Intended: `[state, signal_fail, error_fail, locked]`. |
| `0x040` | 16 | `sf_jumpA` | RW | 14 | s | -8192..8191 | 0 | Step-response measurement: value added to `ctrl_A` during the step. |
| `0x044` | 17 | `sf_jumpB` | RW | 14 | s | -8192..8191 | 0 | Same for `ctrl_B`. |
| `0x048` | 18 | `sf_config` | RW | 5 | u | 0..31 | 0 | Step response: `[0]` start, `[1]` freeze PID A output, `[2]` freeze PID A integrator, `[3]` freeze PID B output, `[4]` freeze PID B integrator (during the step). |

### Lock-in amplifier

| Offset | Idx | Name | R/W | Bits | s/u | Range | Reset | Function |
|---|---|---|---|---|---|---|---|---|
| `0x04C` | 19 | `signal_sw` | RW | 3 | u | 0..7 | 0 (in1) | Input of the lock-in (`signal_i`). See [selector values](#lock-in-input-signal_sw). |
| `0x050` | 20 | `signal_i` | R | 14 | s | -8192..8191 | — | Lock-in input. Frozen by `read_ctrl[0]`. |
| `0x054` | 21 | `sg_amp0` | RW | 5 | u | 0..31 (UI: 0..19) | 0 | Gain of `Xo`, `Yo`: ×2^`sg_amp0`. |
| `0x058` | 22 | `sg_amp1` | RW | 4 | u | 0..15 (UI: 0..9) | 0 | Gain of `F1o`: ×2^`sg_amp1`. |
| `0x05C` | 23 | `sg_amp2` | RW | 4 | u | 0..15 (UI: 0..9) | 0 | Gain of `F2o`. |
| `0x060` | 24 | `sg_amp3` | RW | 4 | u | 0..15 (UI: 0..9) | 0 | Gain of `F3o`. |
| `0x064` | 25 | `lpf_F0` | RW | 6 | u | 0..63 | 32 | Low-pass filter of X and Y: `[3:0]` time constant, `[5:4]` order. See [bit fields](#lpf_f0-to-lpf_f3-0x064-0x070). |
| `0x068` | 26 | `lpf_F1` | RW | 6 | u | 0..63 | 32 | Low-pass filter of F1. |
| `0x06C` | 27 | `lpf_F2` | RW | 6 | u | 0..63 | 32 | Low-pass filter of F2. |
| `0x070` | 28 | `lpf_F3` | RW | 6 | u | 0..63 | 32 | Low-pass filter of F3. |
| `0x074` | 29 | `error_sw` | RW | 3 | u | 0..7 | 0 | Signal used as `error`. See [selector values](#error-signal-error_sw). |
| `0x078` | 30 | `error_offset` | RW | 14 | s | -8192..8191 | 0 | Subtracted from the selected signal: `error = sel − error_offset` (no saturation, 14-bit wrap; l. 548-551). |
| `0x07C` | 31 | `error` | R | 14 | s | -8192..8191 | — | Error signal. Frozen by `read_ctrl[0]`. |
| `0x080` | 32 | `error_mean` | R | 32 | s | int32 | — | Sum of `error` over 2²⁷ ticks (1.074 s) / 2⁹. Mean in counts = `error_mean / 2^18` (`src/lock.c` l. 309). |
| `0x084` | 33 | `error_std` | R | 32 | s | int32 | — | Sum of `|error|²` over 2²⁷ ticks / 2²². Mean square = `error_std / 32`; std = √(mean square − mean²) (`src/lock.c` l. 310-311). |
| `0x088` | 34 | `mod_out1` | RW | 14 | s | -1..8191 | −1 | Amplitude of the modulation (`cos_ref`) added to OUT1. **Negative = off.** Added amplitude ≈ `mod_out1 / 2` counts (see [App.md](App.md#modulation-generator)). |
| `0x08C` | 35 | `mod_out2` | RW | 14 | s | -1..8191 | −1 | Same for OUT2, with `sin_ref`. |
| `0x090` | 36 | `gen_mod_phase` | RW | 12 | u | 0..2519 | 0 | Phase of `cos_1f`, `cos_2f`, `cos_3f` with respect to `cos_ref`, in units of 360°/2520 = 0.143°. |
| `0x094` | 37 | `gen_mod_hp` | RW | 14 | u | 0..16383 | 0 | Modulation period: f = 125 MHz / (2520 · (`gen_mod_hp` + 1)) → 49.603 kHz .. 3.03 Hz. |
| `0x0C0` | 48 | `sin_ref` | R | 14 | s | ±4094 | — | Sine reference (quadrature). |
| `0x0C4` | 49 | `cos_ref` | R | 14 | s | ±4094 | — | Cosine reference (phase 0). |
| `0x0C8` | 50 | `cos_1f` | R | 14 | s | ±4094 | — | Cosine at 1f, phase-shifted by `gen_mod_phase`. |
| `0x0CC` | 51 | `cos_2f` | R | 14 | s | ±4094 | — | Cosine at 2f, phase-shifted. |
| `0x0D0` | 52 | `cos_3f` | R | 14 | s | ±4094 | — | Cosine at 3f, phase-shifted. |
| `0x0EC` | 59 | `X_28` | R | 28 | s | ±2²⁷ | — | Demodulated in-phase component (from **`cos_ref`**, `lock.v` l. 761), before `sg_amp0`. Frozen by `read_ctrl[0]`. |
| `0x0F0` | 60 | `Y_28` | R | 28 | s | ±2²⁷ | — | Demodulated quadrature component (from **`sin_ref`**). Frozen. |
| `0x0F4` | 61 | `F1_28` | R | 28 | s | ±2²⁷ | — | Demodulated with `cos_1f`. Frozen. |
| `0x0F8` | 62 | `F2_28` | R | 28 | s | ±2²⁷ | — | Demodulated with `cos_2f`. Frozen. |
| `0x0FC` | 63 | `F3_28` | R | 28 | s | ±2²⁷ | — | Demodulated with `cos_3f`. Frozen. |

The 28-bit outputs scale as `X_28 ≈ A · 2^11`, where `A` is the amplitude (in counts) of the component of
`signal_i` in phase with `cos_ref` (derived from the RTL, `lock.v` l. 732-761; the same factor is used by
`control_finn.py` `get_XY()`: `V = X_28 / 2^11 / 8192`).

### Ramp (scan)

| Offset | Idx | Name | R/W | Bits | s/u | Range | Reset | Function |
|---|---|---|---|---|---|---|---|---|
| `0x098` | 38 | `ramp_A` | R | 14 | s | -8192..8191 | — | Ramp output A. |
| `0x09C` | 39 | `ramp_B` | R | 14 | s | -8192..8191 | — | Ramp output B = `ramp_A · ramp_B_factor / 4096`. |
| `0x0A0` | 40 | `ramp_step` | RW | 32 | u | 0..2³²−1 | 0 | Ticks per ramp step **minus one**: each value of the ramp lasts `ramp_step + 1` ticks. |
| `0x0A4` | 41 | `ramp_low_lim` | RW | 14 | s | -8192..8191 | −5000 | Lower limit of the ramp ("scan floor"). |
| `0x0A8` | 42 | `ramp_hig_lim` | RW | 14 | s | -8192..8191 | 5000 | Upper limit of the ramp ("scan ceil"). |
| `0x0AC` | 43 | `ramp_reset` | RW | 1 | u | 0..1 | 0 | 1 = hold the ramp at 0 (written as `|sys_wdata`: any non-zero value is 1). |
| `0x0B0` | 44 | `ramp_enable` | RW | 1 | u | 0..1 | 0 | Ramp enable ("Scan enable" of the Ramp panel). The ramp runs only if this **and** the effective ramp enable of `lock_control` are 1. |
| `0x0B4` | 45 | `ramp_direction` | RW | 1 | u | 0..1 | 0 | Starting direction (triangle) / direction of the sawtooth. |
| `0x0B8` | 46 | `ramp_sawtooth` | RW | 1 | u | 0..1 | 0 | 1 = sawtooth, 0 = triangle. |
| `0x0BC` | 47 | `ramp_B_factor` | RW | 14 | s | -4096..4096 (RTL: -8192..8191) | 4096 | Ratio `ramp_B / ramp_A`, 4096 = 1. |

Ramp period: `T = (ramp_hig_lim − ramp_low_lim) · (ramp_step + 1) · 8 ns · (2 − ramp_sawtooth)`
(`index.html` l. 1844, consistent with `gen_ramp.v`).

### Inputs, outputs and monitor values

| Offset | Idx | Name | R/W | Bits | s/u | Range | Function |
|---|---|---|---|---|---|---|---|
| `0x0D4` | 53 | `in1` | R | 14 | s | -8192..8191 | Fast input IN1 (ADC, after the 2's complement conversion of the top). |
| `0x0D8` | 54 | `in2` | R | 14 | s | -8192..8191 | Fast input IN2. |
| `0x0DC` | 55 | `out1` | R | 14 | s | -8192..8191 | Fast output OUT1 (after adding the modulation and saturating). |
| `0x0E0` | 56 | `out2` | R | 14 | s | -8192..8191 | Fast output OUT2. |
| `0x0E4` | 57 | `oscA` | R | 14 | s | -8192..8191 | Signal sent to scope channel A. |
| `0x0E8` | 58 | `oscB` | R | 14 | s | -8192..8191 | Signal sent to scope channel B. |
| `0x100` | 64 | `cnt_clk` | R | 32 | u | — | Low 32 bits of a 50-bit tick counter (frozen by `read_ctrl[0]`; counts only while `read_ctrl[1] = 1`, otherwise 0). |
| `0x104` | 65 | `cnt_clk2` | R | 32 | u | 0..2¹⁸−1 | High 18 bits of the same counter. |
| `0x108` | 66 | `read_ctrl` | RW | 3 | u | 0..7 | `[0]` freeze the copies of `signal_i`, `error`, `X_28`..`F3_28`, `ctrl_A`, `ctrl_B`, `cnt_clk*` (v2.3.17: also held during each bus read); `[1]` run the tick counter; `[2]` unused. Reset 0. |
| `0x174` | 93 | `aux_A` | RW | 14 | s | -8192..8191 | Constant usable as a signal in several selectors (and as a manual offset on an output). Reset 0. |
| `0x178` | 94 | `aux_B` | RW | 14 | s | -8192..8191 | Same. Reset 0. |

### PID A and PID B

PID B is identical to PID A at offset `+0x34` (indices +13).

| Offset A / B | Idx A / B | Name | R/W | Bits | s/u | Range | Reset | Function |
|---|---|---|---|---|---|---|---|---|
| `0x10C` / `0x140` | 67 / 80 | `pidX_sw` | RW | 5 (4 used) | u | 0..15 | 0 (error) | PID input. Only bits `[3:0]` reach the selector (`muxer4`): 16..31 behave as 0..15. See [selector values](#pid-inputs-pida_sw-pidb_sw). |
| `0x110` / `0x144` | 68 / 81 | `pidX_PSR` | RW | 3 | u | 0..4 | 3 | Proportional divider: 0 /1, 1 /8, 2 /64, 3 /1024, 4 /4096. Others → /1. |
| `0x114` / `0x148` | 69 / 82 | `pidX_ISR` | RW | 4 | u | 0..9 | 8 | Integrator divider 2^n, n = 0,3,6,10,13,16,20,23,26,30. Others → 2⁰. |
| `0x118` / `0x14C` | 70 / 83 | `pidX_DSR` | RW | 3 | u | 0..5 | 0 | Derivative: averages 2^n samples, n = 0,3,6,10,13,16. Others → 2⁰. |
| `0x11C` / `0x150` | 71 / 84 | `pidX_SAT` | RW | 14 (8 used) | u | 0..13 | 13 | Saturation of the integral term at ±2^`SAT` counts (13 → ±1 V). |
| `0x120` / `0x154` | 72 / 85 | `pidX_sp` | RW | 14 | s | -8192..8191 | 0 | Set point. |
| `0x124` / `0x158` | 73 / 86 | `pidX_kp` | RW | 14 | s | -8192..8191 | 0 | Proportional gain. |
| `0x128` / `0x15C` | 74 / 87 | `pidX_ki` | RW | 14 | s | -8192..8191 | 0 | Integral gain. |
| `0x12C` / `0x160` | 75 / 88 | `pidX_kd` | RW | 14 | s | -8192..8191 | 0 | Derivative gain. |
| `0x130` / `0x164` | 76 / 89 | `pidX_in` | R | 14 | s | -8192..8191 | — | PID input (output of the selector). |
| `0x134` / `0x168` | 77 / 90 | `pidX_out` | R | 14 | s | -8192..8191 | — | PID output **after** the lock enable (0 while the PID is disabled). |
| `0x138` / `0x16C` | 78 / 91 | `pidX_ctrl` | RW | 3 | u | 0..7 | 0 | `[0]` integrator reset, `[1]` freeze output, `[2]` freeze integrator. |
| `0x13C` / `0x170` | 79 / 92 | `ctrl_A` / `ctrl_B` | R | 14 | s | -8192..8191 | — | Control signal: `pidX_out + ramp_X + sf_jumpX` saturated to 14 bits (`lock.v` l. 273-277). Frozen by `read_ctrl[0]`. |

### Streaming

| Offset | Idx | Name | R/W | Bits | s/u | Range | Reset | Function |
|---|---|---|---|---|---|---|---|---|
| `0x17C` | 95 | `stream_ip` | RW | 32 | u | IPv4 | 0 | IP of the computer that receives the stream, little-endian: `a.b.c.d` = `a + b·2⁸ + c·2¹⁶ + d·2²⁴`. |
| `0x180` | 96 | `stream_port` | RW | 32 | u | 0..65535 | 6000 | TCP port of the receiver. |
| `0x184` | 97 | `stream_rate` | RW | 17 | u | 64..65536 | 128 | Decimation of the scope while streaming (the UI offers 64, 128, 256, 512, 1024, 8192, 65536). |
| `0x188` | 98 | `stream_cmd` | RW | 32 | u | 0..1 | 0 | 1 = streaming running. Bit 0 also tells the scope to use `stream_rate` as decimation. |

### Bit fields

#### `lock_control` (0x018)

Design and state machine: [`lock_control.md`](../lock_in+pid_harmonic/doc/lock_control.md) §2.1-2.2
(`lock/lock_ctrl.v`). Summary:

| Bit | Parameter of the C controller | Meaning |
|---|---|---|
| 0 | `lock_ctrl_aux_lock_now` | Lock request, immediate: a 0→1 edge goes to LOCKED. |
| 1 | `lock_ctrl_aux_launch_lock_trig` | Lock request on trigger: a 0→1 edge arms (ARMED); the trigger locks. |
| 1:0 = 00 | — | Release: back to IDLE. |
| 2 | `lock_ctrl_aux_pidB_enable_ctrl` | Manual enable of PID B (IDLE, ARMED). |
| 3 | `lock_ctrl_aux_pidA_enable_ctrl` | Manual enable of PID A. |
| 4 | `lock_ctrl_aux_ramp_enable_ctrl` | Manual enable of the ramp. |
| 5 | `lock_ctrl_aux_set_pidB_enable` | PID B enable while LOCKED. |
| 6 | `lock_ctrl_aux_set_pidA_enable` | PID A enable while LOCKED. |
| 7 | `lock_ctrl_aux_set_ramp_enable` | Ramp enable while LOCKED. |
| 9:8 | `lock_ctrl_aux_trig_type` | 0 off (only Lock Now), 1 time, 2 level, 3 level after time. |
| 10 | `lock_ctrl_aux_lock_trig_rise` | Level trigger on rising (1) / falling (0) crossing. |

A change of bits `[4:2]` while LOCKED releases the lock. The reset value 1148 (`0x47C`) has the three
manual enables and `set_pidA`/`set_pidB` on, trigger type 0 and rising level.

#### `lock_status` (0x01C)

| Bits | Meaning |
|---|---|
| 0 | armed (state ARMED) |
| 1 | locked (state LOCKED) |
| 2 | effective PID B enable |
| 3 | effective PID A enable |
| 4 | effective ramp enable of the lock control (the ramp also needs `ramp_enable`, 0x0B0) |
| 7:5 | 0 |
| 15:8 | number of entries into LOCKED, modulo 256 |

Example from the board: `0x110A` = locked, PID A on, 17 locks (`reportes/lock-in_pid_h_lock_test/2026-10-08_22:45:40_lock.md` §3).

#### `trig_sw` (0x00C)

`trigger_signals` in `lock.v` l. 343-351. The scope external trigger is a pulse of 8 ticks
(`lock/trigger_input.v`, N = 3) on every rising edge of `|(trigger_signals & trig_sw)`. The UI selects one
bit at a time ("Ext Trig" in the Oscilloscope panel).

| Bit | Value | UI label | Signal |
|---|---|---|---|
| — | 0 | None | — |
| 0 | 1 | Pin | Digital input DIO0_P (`exp_p_io[0]`) of the extension connector |
| 1 | 2 | Scan floor | Ramp reaches `ramp_low_lim` |
| 2 | 4 | Scan ceil | Ramp reaches `ramp_hig_lim` |
| 3 | 8 | harmonic mod. | Start of each period of the modulation |
| 4 | 16 | Square mod. | Not implemented (always 0) |
| 5 | 32 | Out of lock | Re-lock condition (debounced) |
| 6 | 64 | Jump trigger | Start of the step of the step-response measurement |
| 7 | 128 | Lock control trig | One-tick pulse when the lock state machine enters LOCKED (used by *Capture Lock*) |

#### `lpf_F0` to `lpf_F3` (0x064-0x070)

From `lock.v` l. 706-717 and `lock/LP_filter3.v`. Each line has two cascaded first-order filters A and B;
a filter is bypassed when bits `[5:4]` of its own 6-bit `tau` input are not 00.

| `[5:4]` | Filter A | Filter B | Order (UI) |
|---|---|---|---|
| 00 | bypass | bypass | 0 = OFF |
| 01 | bypass | active | 1 |
| 10 | active | active | 2 |
| 11 | active | bypass | 1 (not offered by the UI) |

`[3:0]` = n: time constant τ = 8 ns · 2^(14+n) (131 µs .. 4.29 s), cut-off f = 1/(2πτ) (1.21 kHz .. 37 mHz).
The C controller writes `order << 4 | tau` (`src/lock.c` l. 145-148). Reset value 32 = order 2, n = 0.

### Selector values

The labels are the ones of the UI (`index.html`) and of `reg_labels` in
`resources/remote_control/http_version/control_finn.py`; the signals come from the muxers of `lock.v`.

#### Oscilloscope channels (`oscA_sw`, `oscB_sw`)

`muxer_reg5` (`lock.v` l. 282-337). 25..31 → 0.

| Value | Signal | Value | Signal | Value | Signal |
|---|---|---|---|---|---|
| 0 | 0 | 9 | pidB_in | 18 | Yo |
| 1 | in1 | 10 | PID A out (before the lock enable) | 19 | F1o |
| 2 | in2 | 11 | PID B out (before the lock enable) | 20 | F2o |
| 3 | error | 12 | sin_ref | 21 | F3o |
| 4 | ctrl_A | 13 | cos_ref | 22 | signal_i |
| 5 | ctrl_B | 14 | cos_1f | 23 | out1 |
| 6 | Ramp A | 15 | cos_2f | 24 | out2 |
| 7 | Ramp B | 16 | cos_3f | | |
| 8 | pidA_in | 17 | Xo | | |

#### Fast outputs (`out1_sw`, `out2_sw`)

`muxer4` (`lock.v` l. 368-414).

| Value | Signal | Value | Signal |
|---|---|---|---|
| 0 | 0 | 8 | cos_ref |
| 1 | in1 | 9 | sin_ref |
| 2 | in2 | 10 | PID A out |
| 3 | in1 − in2 | 11 | PID B out |
| 4 | error | 12 | ctrl_A |
| 5 | cos_1f | 13 | ctrl_B |
| 6 | cos_2f | 14 | aux_A |
| 7 | cos_3f | 15 | aux_B |

#### Lock-in input (`signal_sw`)

0 in1, 1 in2, 2 in1 − in2, 3 cos_ref, 4 sin_ref, 5 cos_1f, 6 aux_A, 7 Ramp A (`lock.v` l. 516-529).

#### Error signal (`error_sw`)

0 → 0, 1 Xo, 2 Yo, 3 F1o, 4 F2o, 5 F3o, 6 in1, 7 in1 − in2 (`lock.v` l. 533-546).

#### PID inputs (`pidA_sw`, `pidB_sw`)

0 error, 1 Xo, 2 Yo, 3 F1o, 4 F2o, 5 F3o, 6 signal_i, 7 Ramp A, 8 in1 − in2, 9 in1, 10 in2, 11 aux_A,
12 aux_B, 13 cos_ref, 14 sin_ref, 15 → 0 (`lock.v` l. 869-882, the same for PID B).

#### Lock trigger signal (`lock_trig_sw`)

0 error, 1 Xo, 2 Yo, 3 F1o, 4 F2o, 5 F3o, 6-8 → 0 (square lock-in, not implemented), 9 signal_i,
10 Ramp A, 11 aux_A, 12 in1, 13 in2, 14 in1 − in2, 15 PID A out (before the enable) (`lock.v` l. 623-644).

`in1 − in2` is saturated to 14 bits (`sat14`, `lock.v` l. 513-514).

## Oscilloscope (0x40100000)

Red Pitaya 2.0 scope (`fpga/rtl/rtl/classic/rp_scope_com.v`, `rp_scope_cfg.v`), with three changes of
this App: decimation widened to 20 bits, `osc_ctrl_i` input from the lock module, and `sys_rdata` held
outside reads (streaming fix, v2.3.10). Registers 0..19 are the ones known by `c/osc` and `c/osc.txt`
(same order as the 0.9x scope); the rest come from `rp_scope_cfg.v` (writes l. 350-415, reads l. 440-520)
and `src/fpga.h`.

| Offset | Idx | Name (`osc.txt`) | R/W | Bits | Function |
|---|---|---|---|---|---|
| `0x00` | 0 | `conf` | RW | — | Write: `[0]` arm, `[1]` reset the write state machine, `[3]` arm keep, `[5]` independent mode. Read (`adc_state`): `[2]` trigger received (sticky until arm/reset), `[4]` acquisition done (2.0 only). |
| `0x04` | 1 | `TrgSrc` | RW | 5 | Trigger source: 1 now (manual), 2/3 ch A rising/falling, 4/5 ch B rising/falling, **6/7 external rising/falling** (= lock trigger, `trig_sw`), 8/9 ASG (unused). Reads 0 after the trigger. **2.0: bit 5 reads the trigger lock** (see 0x94). |
| `0x08` | 2 | `ChAth` | RW | 14 | Trigger level of ch A (signed). |
| `0x0C` | 3 | `ChBth` | RW | 14 | Trigger level of ch B (signed). |
| `0x10` | 4 | `TrgDelay` | RW | 32 | Decimated samples written after the trigger. |
| `0x14` | 5 | `Dec` | RW | **20** | Decimation. The controller uses 1, 8, 64, 128, 256, 512, 1024, 8192, 65536, 524288 (`src/fpga.c` l. 509-545). RedPitaya: 17 bits. |
| `0x18` | 6 | `CurWpt` | R | 14 | Current write pointer. |
| `0x1C` | 7 | `TrgWpt` | R | 14 | Write pointer at the trigger. |
| `0x20` | 8 | `ChAHys` | RW | 14 | Trigger hysteresis of ch A (the controller writes 0x3F). |
| `0x24` | 9 | `ChBHys` | RW | 14 | Trigger hysteresis of ch B. |
| `0x28` | 10 | `AvgEn` | RW | 1(+1) | `[0]` average inside the decimation (ch A); 2.0 adds `[1]` high resolution and the same bits for other channels at `[8]`, `[16]`, `[24]`. |
| `0x2C` | 11 | `PreTrgCnt` | R | 32 | 2.0: count of samples written since the arm (`adc_we_cnt`). |
| `0x30`..`0x3C` | 12..15 | `ChAEqFil1..4` | RW | 18/25 | Equalization filter of ch A: AA, BB, KK, PP. |
| `0x40`..`0x4C` | 16..19 | `ChBEqFil1..4` | RW | 18/25 | Equalization filter of ch B. |
| `0x94` | (37) | trigger unlock | W | 1 | **2.0 only.** After each trigger the scope locks its trigger; writing 1 to bit 0 unlocks it. The C controller does it before each acquisition (`src/fpga.c` `osc_fpga_set_trigger()`, `src/fpga.h` `trigger_lock_ctr`). **Not accessible from `c/osc`** (see the differences below). |
| `0x98` | — | filter bypass | RW | 4 | Bypass of the equalization filters (OR-ed with `osc_ctrl[1:0]` of the lock). |
| `0x10000` | — | ch A buffer | R | 16 × 16384 | Samples of ch A, 16-bit sign-extended in 2.0 (14 valid bits). |
| `0x20000` | — | ch B buffer | R | 16 × 16384 | Samples of ch B. |

Maximum time span of an acquisition: 16384 · 8 ns · Dec (0.131 ms at Dec 1, 68.7 s at Dec 524288).

Lock `osc_ctrl_w` → scope `osc_ctrl_i` (`lock.v` l. 251, `rp_scope_com.v` l. 194-207):
`[1:0]` = `osc_ctrl` (filter bypass), `[2]` = `stream_cmd[0]` (use the streaming decimation),
`[19:3]` = `stream_rate`, `[20]` = end of streaming pulse.

## Other blocks

- **Slow analog outputs (AO0-AO3):** the classic 250 MHz PWM is driven by `pwm_cfg_a..d` of the lock module
  (`red_pitaya_top.sv` l. 416-428), but in `lock.v` `slow_out1/2` are tied to mid-scale and the selectors
  `slow_out3_sw`/`slow_out4_sw` are not registers (undeclared nets). There are no slow-output registers in
  the map. See the differences below.
- **Extension connector:** DIO0_P = external trigger input (bit 0 of `trig_sw`), DIO6_N = ramp direction
  output, DIO7_N = digital modulation output (always 0, `lock.v` l. 586). If CAN is enabled in the
  housekeeping, DIO6_N/DIO7_N go back to CAN TX (`red_pitaya_top.sv` l. 539-546).

## Register description files (`lock.txt`, `osc.txt`)

`lock_in+pid_harmonic/c/lock.txt` and `c/osc.txt` are CSV files `name,index,signed,read_only,min,max`
generated by `resources/config_tool.py` from the same table that generates the register blocks of
`lock.v`, `c/lock.c`, `c/osc.c` and `src/`. They are installed with the App and served by nginx at
`http://rp-XXXXXX.local/lock_in+pid_harmonic/c/lock.txt` and `.../c/osc.txt`; `control_finn.py` reads them
to know the names. `c/lock` and `c/osc` have the same tables compiled in.

The previous `doc/README.md` (a copy of `lock.txt` as a table) was replaced by this page.

## Differences found between the files and the RTL

Checked against `lock.v`, `lock/*.v`, `red_pitaya_top.sv`, `rp_scope_cfg.v`, `rp_scope_com.v`,
`src/fpga.h`, `src/fpga_lock.h`. The tables above follow the RTL. Reported to devAgent (see
`docAgent.md`).

| # | File | Item | File says | RTL does |
|---|---|---|---|---|
| 1 | `c/osc.txt`, `c/osc.c` | `Dec` max | 131071 (17 bits) | 20 bits; the App uses up to 524288. `c/osc` does not check the max, so writing 524288 works. |
| 2 | `c/osc.txt`, `c/osc.c` | trigger unlock 0x94 | not present (20 registers, up to 0x4C) | needed on the 2.0 scope to re-arm the trigger (see [Remote.md](Remote.md#limitations-of-osc-on-the-20-fpga)) |
| 3 | `c/lock.txt` | `osc_ctrl` max | 4294967295 | 2-bit register (0..3) |
| 4 | `c/lock.txt` | `pidA_sw`, `pidB_sw` max | 31 | only bits `[3:0]` are used (0..15) |
| 5 | `c/lock.txt` | `rl_state` | read-only 0..31 | constant 0 (`lock.v` l. 135) |
| 6 | `c/lock.txt` | `lock_trig_time` max | 4294967295 | only bits `[30:0]` are compared (`lock_ctrl.v`): values ≥ 2³¹ alias to `value − 2³¹` |
| 7 | `c/lock.txt` | `pidX_SAT` | 0..13 | 14-bit register, only `[7:0]` used; consistent in practice |
| 8 | `lock.v` / `src/fpga_lock.h` comments | `X_28` / `Y_28` | "from sin_ref" / "from cos_ref" | X from `cos_ref`, Y from `sin_ref` (`lock.v` l. 761-762) |
| 9 | `lock.v` / `fpga_lock.h` comments | `ctrl_B` | "pidA_out + ramp_B" | `pidB_out + ramp_B + sf_jumpB` |
| 10 | `src/fpga.h` comment | `data_dec` | "bits [16:0]" | 20 bits |
| 11 | `fpga/README.md` | scope decimation | "17-bit decimation (max 64k)" | 20 bits (max 512k), as said in the CHANGELOG of v2.3.10 |
