# Using the App from the web interface

How to use `lock_in+pid_harmonic` **v2.3.31** (branch `master`) from the browser, panel by panel, and the usual procedures:
scan, see a peak, get an error signal with the lock-in, close a lock and check it. Technical data of each
instrument is in [App.md](App.md); registers in [FPGA.md](FPGA.md).

- [Opening the App](#opening-the-app)
- [Layout of the page](#layout-of-the-page)
- [Panels](#panels)
  - [Toolbar](#toolbar) ([Reset zoom: whole period / rising half](#reset-zoom-whole-period--rising-half)) ·
    [Oscilloscope](#oscilloscope) · [Outputs](#outputs) · [Lock-in modules](#lock-in-modules) ·
    [Ramp Controller](#ramp-controller) ([Tabs period and freq](#tabs-period-and-freq), [Lock osc. screen](#lock-osc-screen)) ·
    [PIDs modules](#pids-modules) · [Lock Control](#lock-control) · [Streaming](#streaming) ·
    [Right panels and displays](#right-panels-and-displays) · [Slow scans](#slow-scans)
- [Typing values with units](#typing-values-with-units)
- [Procedures](#procedures)
  1. [Scan and see the response of the system](#1-scan-and-see-the-response-of-the-system)
  2. [Configure the lock-in to get an error signal](#2-configure-the-lock-in-to-get-an-error-signal)
  3. [Close the lock (Trigger Lock / Lock Now)](#3-close-the-lock)
  4. [Check the lock and release it](#4-check-the-lock-and-release-it)
- [Saving and loading configurations](#saving-and-loading-configurations)
- [Saving data](#saving-data)
- [Several clients and Restart](#several-clients-and-restart)
- [Known limitations of the interface](#known-limitations-of-the-interface)

The screenshots were taken on RP2 (RedPitaya_OS 2.04-35) with v2.3.24 (the panels, the lock captures, the
GIF and the Config dialog), v2.3.14-v2.3.17 (the two Time trigger fields, the config load window, the
Choose from graph warning and the Restart dialog) and v2.3.31 (the *Ramp Controller* tabs, *Lock osc. screen* and
*Reset zoom*: board test `reportes/lock-in_pid_h/2026-11-13_1439_v2331.md`, Apps root), against a
simulated peak made by `dummy_simulator` on a second board, with the test configurations
`test_files/lock_in+pid_harmonic__lock_mode.json` and `__scan_mode.json` (see [Procedures](#procedures)). Some
screenshots taller than the browser window are two screenshots of the same page joined.

## Opening the App

Install the App (see the [README](../README.md#installation)) and open
`http://rp-XXXXXX.local/lock_in+pid_harmonic/` (or choose it in the main menu of the Red Pitaya). The page
starts the App (loads the FPGA and the C controller) and, with **Load last config on init** checked (default,
Config dialog, since v2.3.27), restores the last settings used in this browser (any tab); unchecked, the App starts
with its default parameters (see [Saving and loading configurations](#saving-and-loading-configurations)). If the
App is already running (e.g. another tab), the page shows its current state. Use a single tab per board (see [Several clients and Restart](#several-clients-and-restart)).

## Layout of the page

![Layout: scan with Normal trigger on Scan floor (ctrl_A and error), Lock Control open](.Usage/scan_mode_peak_normal_scan_floor.jpg)

- **Top toolbar**: zoom and acquisition buttons.
- **Left column**: the instruments (Oscilloscope, Outputs, Lock Control, Lock-in modules, Ramp Controller, PIDs
  modules, Streaming; Lock Control is below Outputs since v2.3.27). Each title opens or closes its panel.
- **Centre**: the plot (two Y axes, Channel 1 blue and Channel 2 red), the mouse position, and the
  *Harmonic Lock-in* display (X, Y, R, φ, F1, F2, F3).
- **Right column**: the original scope controls (Trigger, Range, Measure, Gain settings) and the Monitor.

Every change is sent to the board when the field loses focus or Enter is pressed (Escape cancels the edit).
Only changed values are sent. A field left empty (e.g. after Backspace) or with an invalid text is **not** sent:
the last value comes back (up to v2.3.15 an emptied field sent 0).

## Panels

### Toolbar

| Button | Action |
|---|---|
| Autoscale | Rescales the **Y axis** to the data on screen, only in the page. Does not end a lock capture. |
| Reset zoom, zoom in/out, pan | Plot navigation. A zoom selects the time window of the acquisition (the decimation is chosen from it). Reset zoom (v2.3.21) sets the window from t = 0 to one period of the ramp (Ext Trig = Scan floor / Scan ceil; with Scan floor and a triangle, a second click gives the rising half, [below](#reset-zoom-whole-period--rising-half); with *Lock osc. screen* on, its window), one period of the modulation (Ext Trig = harmonic mod.) or one whole memory at the current decimation (otherwise); for periods of 1.5 s or more (v2.3.23) the window is 0 … 0.98 × the period, so that every scan is acquired ([Slow scans](#slow-scans)); and Y to −1 … 1 V (raw mode −8192 … 8192); during a lock capture it first ends it, as AUTO, and uses the restored Ext Trig. The Raw Mode button rescales Y the same way. |
| Mouse wheel on the plot (v2.3.22) | Zoom centred on the mouse, 1.5× per step. **No key:** both axes (time and the two Y axes). **SHIFT** held: time axis only (the cursor becomes a horizontal double arrow ↔). **ALT** held: Y axes only (vertical double arrow ↕; in raw mode the Y range is in counts). The time window is sent to the controller once the wheel stops (250 ms), which chooses the decimation as for any zoom; it stays between 20 ns and 68.7 s (one memory at the largest decimation). The Y zoom is only in the page (range 1/2048 … 1000 × full scale). During a lock capture (Capture Lock) the wheel zoom is only in the page and does not touch the scope; ending the capture restores the window saved before it. The wheel on the number fields is not affected (SHIFT ×10, CTRL ×100). With *Lock osc. screen* on (v2.3.31) the wheel without keys zooms Y only and the time zoom (SHIFT, box, X±) changes the ramp limits instead ([Lock osc. screen](#lock-osc-screen)). |
| Channel 1 / Channel 2 | Show or hide each channel. |
| Stop | Stops the acquisition. |
| Save Data | Plot data as Python/Numpy, Matlab/Octave or CSV ([Saving data](#saving-data)). |
| Config | Save / load configurations ([below](#saving-and-loading-configurations)). |
| Raw Mode | Values in counts (`int`) instead of volts. Also the *Level* of the scope trigger (field, slider and line; −8192 … 8191, unit `counts`): switching Raw Mode converts it (counts = V × 8192 / full scale) and sets Y to −8192 … 8192 / −1 … 1 V. Before v2.3.29 the level in Raw Mode was taken as volts by the controller (Normal / Single did not trigger). |
| Averaging | Average inside the decimation. |
| **AUTO** | Auto-set of the scope in the controller (time range, trigger, Y range). Ends a lock capture. Not the same as *Autoscale*. The trigger level is set to the middle of the signal (since v2.3.30 also with a calibration offset of the input; whole counts in Raw Mode). |

#### Reset zoom: whole period / rising half

Since v2.3.31 (port of `lock_in+pid_plus` 2.2.0), with *Source* = External, *Ext Trig* = **Scan floor** and a
**triangle** ramp (and *Lock osc. screen* off), **each click of Reset zoom alternates** between the whole period and
the rising half (`resetZoomCycleNext()`, `index.html` l. 3379, used by `resetZoom()`, l. 6255):

1. first click: 0 … T (one whole period, as before; 0 … 0.98 T for T ≥ 1.5 s, see [Slow scans](#slow-scans));
2. next click: **0 … T/2**, the rise from the scan floor to the top (a triangle always rises after the floor,
   [App.md](App.md#ramp-generator-scan));
3. next click: whole period again, and so on, while the zoom is not touched.

Anything else in between starts the cycle again, so the next click gives the whole period: a zoom by hand (box, wheel
with or without SHIFT / ALT, pan, X± / Y±, Autoscale, the scope presets), a change of the trigger (*Source*, *Mode*,
*Ext Trig*, *Edge*) or of the ramp (any tab, the checkboxes, the zoom of *Lock osc. screen*, another client, a config
load: the parameters are compared too), or a window on the plot different from the one of the last click.

With *Scan ceil* (its first half after the trigger is the fall), a **sawtooth**, *harmonic mod.* or another *Ext
Trig* or *Source*, Reset zoom gives one period / one memory on every click, as before; with *Lock osc. screen* on, it
gives the window of Lock osc. screen. Measured on the board (v2.3.31, ±4000 at 100 Hz, triangle): four clicks gave
0 … 9.984 / 4.992 / 9.984 / 4.992 ms; after a SHIFT + wheel zoom the next click gave 9.984 ms again; sawtooth and Scan
ceil: always the whole period (9.985 / 9.984 ms); *harmonic mod.*: 0 … 20.16 µs (one period of the 49.6 kHz
modulation) on every click.

![Reset zoom, second click: the rising half 0 … 4.992 ms of a 100 Hz triangle (v2.3.31; blue in1, red Ramp A)](.Usage/reset_zoom_click2_rising_half.jpg)

When a click changes the time units (e.g. from a window in seconds to ms) the server repeats the new window in every
`GET /data` until the next POST; since v2.3.31 the page applies that once and never over a window that it has just
set itself ([Structure.md](Structure.md#time-window-of-the-plot-and-force-x)). Board test: 10/10 second clicks from
an axis in seconds stayed at 0 … 4.992 ms, also 3 s and 6 s later.

### Oscilloscope

![Oscilloscope panel](.Usage/panel_oscilloscope_scan.jpg)

- **OscA / OscB**: signal shown on Channel 1 / Channel 2 (any of 25 internal signals:
  in1, in2, error, ctrl_A, ctrl_B, Ramp A/B, PID inputs/outputs, references, Xo, Yo, F1o..F3o, signal_i,
  out1, out2). The fast inputs are seen with `in1`/`in2`.
- **Ext Trig**: event used when the scope trigger *Source* is *External*: None, Pin (DIO0_P), Scan floor,
  Scan ceil, harmonic mod. (start of each modulation period), Out of lock, Jump trigger, Lock control trig
  (the lock event; used by Capture Lock). *Square mod.* is not implemented (always 0 in the FPGA) and is not in the
  menu since v2.3.25.
  Since v2.3.24, picking an Ext Trig other than the current one and not *None* also sets the *Trigger* panel to
  *Source* = External and *Mode* = Normal (one POST). *None* changes nothing else; *Config load*, the end of a
  Capture Lock, *Reset zoom* and *AUTO* keep their own trigger settings.
- **Presets** (v2.3.24): small buttons below Ext Trig that set OscA|OscB in one click: `in1|in2`, `in1|ctrl`
  (in1, ctrl_A), `X|Y` (Xo, Yo) in blue; `in1|err` (in1, error), `ctrl|err` (ctrl_A, error) and `usr` in green.
  They change only the two signals: not the zoom, not the trigger, not a lock capture. `usr` is a pair of your
  own: **double click** on it (or a click while it is not configured; dashed border) opens a dialog with the two
  signals; *Accept* saves it in the browser and shows it. The pair is also saved in the configs (*Config*: save and
  download; older configs without it keep the current one). The tooltip of each button names its two signals.
- **More options**: *R|Phase Mode* (disabled in this version) and *Disable anti-aliasing filter* for each
  channel.

![More options](.Usage/panel_oscilloscope_more_options.jpg)

### Outputs

![Outputs and Streaming panels](.Usage/panel_outputs_streaming.jpg)

- **Out1 / Out2**: signal sent to each fast output (±1 V): 0, in1, in2, in1−in2, error, cos_1f, cos_2f,
  cos_3f, cos_ref, sin_ref, PID A out, PID B out, ctrl_A, ctrl_B, aux_A, aux_B. For a lock, Out1 = ctrl_A
  (ramp + PID A) is the usual choice.
- **Slow outputs**: four selectors. **They have no effect in this version** (the slow outputs are not
  driven by the FPGA, see [App.md](App.md#inputs-and-outputs)).

### Lock-in modules

![Lock-in modules panel](.Usage/panel_lockin_modules.jpg)

- **Lock-in input**: signal to demodulate (in1, in2, in1−in2, cos_ref, sin_ref, cos_1f, aux_A, Ramp A).
- **Harmonic oscillator**: *Period* (`gen_mod_hp`, shows τ and f below: 0 → 49.603 kHz) and *Phase* of the
  F1/F2/F3 references (0..2519 = 0..360°).
- **Demodulation**: tabs *X & Y*, *F1*, *F2*, *F3*, each with its low-pass filter (*cut* = τ | f, *order*
  OFF/1/2) and *Amplification* ($\times 2^{n}$).
- **Auxiliar**: *Aux A*, *Aux B* constants, and **Modulation Amplitude** *A Out1* / *A Out2*: amplitude of
  the reference added to OUT1 (`cos_ref`) / OUT2 (`sin_ref`); −1 = off, 0..8191 (≈ value/16384 V).

### Ramp Controller

Since **v2.3.31** (the Ramp Controller of `lock_in+pid_plus` 2.2.0, web page only) the panel has two tabs, *period*
and *freq*, and a *Lock osc. screen* option. The ramp of the FPGA (`gen_ramp.v`, the same file as in pid_plus) and
its registers are the same as before (CHANGELOG v2.3.31). The relation between the registers and the physical ramp
(period, frequency, amplitude, offset) is in [App.md](App.md#ramp-generator-scan).

![Tab period: Ramp period 77 (τ = 9.98 ms, f = 100.16 Hz), limits ±4000, inside the box of the tab; below, Ramp B factor, Lock osc. screen and the four checkboxes in two columns (v2.3.31)](.Usage/ramp_tab_period_box_checkboxes.jpg)

Layout of the panel (top to bottom, `index.html` l. 8536-8733):

- the tabs **period | freq**; the fields of the active tab are inside a box closed by the grey line of the tabs
  (1 px `#dddddd`, CSS `.ramp-tab-pane`, l. 37-46), so it is clear which controls belong to the tab;
- **Ramp B factor** (4096 = 1: ratio of Ramp B to Ramp A; outside the tabs, as before);
- **Lock osc. screen** (checkbox, between two separators, with a short status text below);
- the amplitude (mVpp) and centre (mVdc) of the ramp;
- the four checkboxes in **two columns**: *Scan reset* / *Scan enable* on the left, *Scan direction* / *Sawtooth* on
  the right. *Scan reset* holds the ramp at 0; *Scan enable* runs it (the *Scan enable* button of Lock Control must
  also be on); *Scan direction* is the direction of the sawtooth (a triangle always rises after the scan floor, see
  [App.md](App.md#ramp-generator-scan)); *Sawtooth* unchecked = triangle.

Labels in mV that round to zero show "0 mV", never "-0 mV" (`toFixedNz()`, l. 1999; also V<sub>trg</sub> of the
lock trigger).

#### Tabs period and freq

Only the active tab is visible, so there is only one way of editing the ramp at a time. Clicking the other tab
first applies the edit in progress (as leaving the field) and then **loads the fields of the new tab from the
parameters of the board** (including changes made by another client or a config load); `rampTabSet()`,
`index.html` l. 3666. The last tab used is kept in the browser (`localStorage`, key
`lockin_ramp_tab_lock_in+pid_harmonic`, `ramp_tab_key` l. 3642) and comes back after a reload.

**Tab period**:

| Field | Units | What it does |
|---|---|---|
| **Ramp period** | `ramp_step` (clock ticks per step − 1), or **the whole period** with a unit: `s`, `seg`, `ms`, `us` (`10 ms`, `0.5 s`, `10ms`; decimal point or comma) | A number alone is the step. A period is converted to the step whose whole period *T* (below) is the nearest one (`rampStepForPeriod()` / `rampParseStep()`, l. 3439-3460) |
| **Ramp hig lim**, **Ramp low lim** | counts (8192 = 1 V) | Limits of the ramp. Below each field: the limit in mV. They do not accept `mV` / `V` from the page (see [Known limitations](#known-limitations-of-the-interface)); the *freq* tab does |

The period of *Ramp period* is that of the whole ramp, from scan floor to scan floor:

$$
T = N\,(\mathrm{step}+1)\cdot 8\ \mathrm{ns},\qquad N = \begin{cases} 2\,(\mathrm{hig}-\mathrm{low}) & \text{triangle}\\ (\mathrm{hig}-\mathrm{low})+1 & \text{sawtooth} \end{cases}
$$

so it depends on the limits and on the waveform.

- **Enter or leaving the field** sends the value (one POST) and rewrites the field in steps (`77`, `3905`…). While
  typing nothing is sent; the text below already shows the τ / f of what is typed (a preview). Escape restores the
  previous value.
- A text that is not valid (`10 kg`, `abc`, a negative value), or a period with *Ramp hig lim* = *Ramp low lim*, is
  not sent: a red hint appears below ("? steps, or a period with units: s, ms, us" or "? a period needs Ramp hig
  lim &gt; Ramp low lim", l. 2065-2066) and the last value comes back.
- The step is limited to **0 … 2147483520** ($2^{31}-128$, `ramp_step_max`, l. 3417) and rounded as the float32
  parameter of the controller (above $2^{24}$ only every 2nd, 4th … 128th integer exists): `4294967295` or `1e6 s`
  give 2147483520.
- Mouse wheel ±1, SHIFT ×10, CTRL ×100, both ×1000 (above $2^{24}$ the wheel ±1 does not move the step, see
  [Known limitations](#known-limitations-of-the-interface)).
- Below the field: τ (the whole period) and f of the ramp.
- Checking or unchecking *Sawtooth* with the *period* tab active keeps the step, so the period changes (77 with ±4000:
  9.98 ms in triangle, 4.99 ms in sawtooth).
- No tooltip on the label nor the input; a click on the label "Ramp period" opens the help (l. 1927).

Up to v2.3.30 the field was an `<input type="number">`, so a period with units never reached the page, and the old
conversion took (hig − low) steps, half the period of a triangle; the τ of a sawtooth was one step short.

Measured on the board with v2.3.31 (triangle / sawtooth ±4000): `10 ms` + Enter → step 77 in triangle (τ = 9.98 ms),
155 in sawtooth (τ = 9.99 ms); `4294967295` → 2147483520 (also in sawtooth); `10 kg` restores the value; no POST
while typing, one with Enter. The periods measured on the scope trace with the same page code and the same
`gen_ramp.v` (`lock_in+pid_plus` 2.2.0-rc2, `reportes/lock-in_pid_plus/2026-11-13_0747_v220rc2.md`):

| Waveform, limits (N) | Typed | Step | T | T measured |
|---|---|---|---|---|
| triangle ±4000 (16000) | `10 ms` | 77 | 9.984 ms | 9.98396 ms |
| triangle ±4000 | `0.5 s` | 3905 | 499.968 ms | 0.49998 s |
| sawtooth ±4000 (8001) | `10 ms` | 155 | 9.9852 ms | 9.98526 ms |
| sawtooth ±4000 | `0.5 s` | 7811 | 500.03 ms | 0.49999 s |
| triangle 1000 / −3000 (8000) | `10 ms` | 155 | 9.984 ms | 9.98399 ms |
| sawtooth 1000 / −3000 (4001) | `10 ms` | 311 | 9.9865 ms | 9.98672 ms |

**Tab freq**:

![Tab freq with the ramp of the scan configuration: 15.58603 Hz (step 400, triangle), Amp. p-p 10000 (1221 mVpp), Offset 0 (v2.3.31)](.Usage/ramp_tab_freq_15.59Hz.jpg)

| Field | Units | What it does |
|---|---|---|
| **Frequency** | Hz, or with units: `2.5 kHz`, `10 Hz`, `500 mHz`, `1e3`, `1.5M` (`parseRampFreq()`, l. 3513; `abc`, `-5` are rejected) | Enter (or leaving the field) sets the `ramp_step` whose frequency is the **nearest one** to the value typed, for the current amplitude and waveform (`rampStepForFreq()`, l. 3465). The field then shows the **real** frequency; the text below shows f, τ, the step, the waveform and, if it differs, the value set ("set 100.0000 Hz"). No tooltip. |
| **Amp. p-p** | counts (8192 = 1 V), or `500 mV`, `0.5 V` (`parseRampCounts()`, l. 3504) | Peak-to-peak amplitude = hig − low. Changing it **keeps the frequency** set by the user: the step is recomputed. Text below: mVpp and the two limits in mV. |
| **Offset** | counts, or `mV` / `V` | Centre of the ramp, floor((hig + low)/2). Changing it does not change the frequency. Text below: mVdc. |

- Step, low and high limits go to the board in one POST (`rampSetRegs()`, l. 3740).
- If the amplitude does not fit with the offset (limits −8192 … 8191), the amplitude is reduced (editing the
  Offset, the offset is limited for the amplitude).
- **Mouse wheel on Frequency**: ±1 Hz, SHIFT ±10 Hz, CTRL ±100 Hz, both ±1000 Hz, counted from the **nominal**
  frequency (the one set by the user, not the rounded real one: no drift). Where the integer step can not move
  that little (high frequencies, large amplitudes), or f − 1 Hz would be ≤ 0, the wheel moves the register by
  **one step** in the direction asked (the minimum move of the instrument; it never stays still), and the real
  frequency becomes the new nominal one. At step 0 (the highest frequency for that amplitude) it does not move
  further (`rampFreqWheelTarget()`, l. 3541).
- **Mouse wheel on Amp. p-p / Offset**: ±1, SHIFT ×10, CTRL ×100, both ×1000 counts.
- **Sawtooth** checked or unchecked while the *freq* tab is active (or *Lock osc. screen* is on): the frequency is
  kept and the step is recomputed for the new number of steps (`rampSawtoothKeep()`, l. 3785). With the *period* tab
  active the step is kept, so the frequency changes (triangle → sawtooth roughly doubles it).

Measured on the board (v2.3.31, triangle, report `reportes/lock-in_pid_h/2026-11-13_1439_v2331.md`):

| Input | Registers | Text / real frequency |
|---|---|---|
| (tab opened with the scan configuration) | step 400, ±5000 | 15.58603 Hz = $125\ \mathrm{MHz}/(2\cdot 10000\cdot 401)$ |
| Amp. `8000` (from 10000 at 15.586 Hz) | step 500, ±4000 | 15.594 Hz: the frequency is kept |
| Frequency `100` | step 77, ±4000 | f = 100.1603 Hz, τ = 9.984 ms, "set 100.0000 Hz" |
| wheel +1 / −1 | 76 → 77 | 101.4610 → 100.1603 Hz |
| SHIFT + wheel (±10 Hz) | 70 | 110.0352 Hz |
| CTRL + wheel (±100 Hz) | 36 | 211.1486 Hz |
| SHIFT + CTRL + wheel (±1000 Hz) | 5 | 1302.083 Hz (target 1211 Hz: the nearest reachable step) |
| `2.5 kHz` | 2 | 2.6042 kHz, "set 2.5000 kHz" |
| `500 mHz` | 15624 | 500.0000 mHz, τ = 2.000 s |
| Amp. `500 mV` (at 100 Hz) | step 152, ±2048 | 99.7306 Hz (nominal 100 Hz kept), "500 mVpp" |
| Offset `0.1 V` | −1229 / 2867 | offset 819 = 100.0 mVdc, same f |
| `10 kg` in Frequency | no change | the value comes back, no POST |

The resolution of the frequency depends on the step: $f = 125\ \mathrm{MHz}/(N\,(\mathrm{step}+1))$, so near step 0
the reachable frequencies are far apart (e.g. 2604 → 3906 → 7812 Hz for steps 2, 1, 0 with Amp. 8000).

#### Lock osc. screen

A checkbox below *Ramp B factor* (off by default) that locks the scope screen to the ramp and turns the **time zoom
of the plot into a change of the ramp limits**: zooming on a part of the scan (e.g. around a peak) makes the ramp scan
only that zone, at the same frequency, and the screen shows it over the whole window.

**The window** (`rampLockScreenWindow()`, l. 3835, which uses `resetZoomWindow(.., half)`, l. 3337):

| Waveform | Window | Why |
|---|---|---|
| **Triangle** | **0 … T/2**: the rising half, from the scan floor (t = 0) to the top | in `gen_ramp.v` a triangle always rises after the floor (`floor ? ramp_signal + 1`, l. 157), whatever *Scan direction*: the first half after the trigger is always the rise, so each value of the ramp appears once on the screen |
| **Sawtooth** | **0 … T**: one whole period | the sawtooth goes through each value once per period |
| Sawtooth, T ≥ 1.5 s | 0 … 0.98 T | as *Reset zoom* since v2.3.23, so that the scope is armed again before the next floor ([Slow scans](#slow-scans)). The rising half of a triangle already ends T/2 before the next floor: no 0.98 |

The status text below the checkbox shows the window ("window 0 .. 4.992 ms (rising half: T/2)", "(slow scan: 0.98 T)",
or "(longest memory, the half period is …)" when the window is longer than 68.7 s and is clamped). The axis is set
to that window whenever it differs from it by more than $10^{-4}$ of the window (`ramp_ls_tol`, l. 3646).

![Lock osc. screen on: 100 Hz triangle, Scan floor, window 0 … 4.992 ms = T/2; the peak of in1 (blue) appears once (v2.3.31)](.Usage/lock_osc_screen_triangle_rising_half_100Hz.jpg)

**Turning it on** (`rampLockScreenOn()`, l. 3892):

- the scope trigger becomes *Ext Trig* = **Scan floor**, *Source* = **External**, *Mode* = **Normal** (as when
  choosing an Ext Trig);
- the time window becomes the window of the table above, so t = 0 is the scan floor;
- a *Capture Lock* in progress ends first;
- the text below the checkbox shows the window and "Time zoom (SHIFT+wheel, box, X±) → ramp limits".

**Zoom while it is on** (`rampLockScreenFromX()`, l. 3927, and `rampZoomToLims()`, l. 3602):

| Action on the plot | Effect |
|---|---|
| **SHIFT + wheel**, a **box selection**, the **X− / X+** buttons of *Range* (time zoom) | New `ramp_low_lim` / `ramp_hig_lim`: the values that the ramp has at the two ends of the window zoomed. **Triangle**: the straight line of the rise, $v(t) = \mathrm{low} + \mathrm{amp}\cdot t/(T/2)$, also outside 0 … T/2 (zoom out, pan). **Sawtooth**: the straight line of the sawtooth, extended outside 0 … T. The **frequency of the whole period is kept** (step recomputed with the new N) and the window goes back to the new T/2 (triangle) or T (sawtooth), so the zone chosen fills the screen. |
| The Y part of a box selection | Zooms Y (only in the page), as usual. |
| A box over the **whole width** of the view (within 2 % at each end) | No time zoom: the ramp does not change, only Y is zoomed (`rampZoomIsView()`, l. 3627). |
| **Wheel without keys** | Y only (normally it zooms both axes); **ALT + wheel**: Y only, as before. The registers do not change. |
| **Reset zoom** | Gives the window of Lock osc. screen again. |

The result is limited to −8192 … 8191 with at least 1 count of amplitude.

Measured on the board (v2.3.31, triangle ±4000 at 100 Hz, Channel 2 = Ramp A; each row starts from the result of the
previous one; the model is $v(t)$ above):

| Action | low / hig (model) | step, f | New window |
|---|---|---|---|
| Box 1.0024 … 2.5040 ms | −2394 / 13 (−2393.6 / 12.8) | 259, 99.869 Hz | 0 … 5.007 ms |
| SHIFT + wheel out at 2.5 ms | −2994 / 617 (amplitude ×1.500, centre −1190.5 → −1188.5) | 100.048 Hz | |
| SHIFT + wheel in at 1 ms | −2754 / −347 (model −2753, the point at 1 ms fixed) | | |
| X+ | −3954 / 853 | 129, 100.014 Hz | 0 … 4.999 ms |
| X− | −2512 / −589 | 100.004 Hz | |

![After the box 1.0024 … 2.5040 ms: low −2394, high 13 (Amp. 2407, Offset −1191), step 259, 99.869 Hz; window 0 … 5.007 ms = T/2; red Ramp A (v2.3.31)](.Usage/lock_osc_screen_zoom_box.jpg)

With a **sawtooth** the window is one whole period (checking *Sawtooth* with the freq tab or Lock osc. screen on keeps
the frequency: 100 Hz ±4000 → step 155, window 0 … 9.985 ms). With *Scan direction* = 0 the sawtooth jumps to the high
limit after the floor and falls (seen on the board, the same `gen_ramp.v` as always); the time zoom follows that line.

![Sawtooth with Lock osc. screen: whole period 0 … 9.985 ms; Ramp A (red) falling with Scan direction 0 (v2.3.31)](.Usage/lock_osc_screen_sawtooth_whole_period.jpg)

**The window follows the ramp**: any change of step, limits or waveform (either tab, the wheel on the fields,
another client, a config load) sets the window again (only when the ramp changed; `rampLockScreenSync()`, l. 3857).
The trace is cleared only if the window really changes: a zoom that keeps the frequency keeps the acquisition in
progress. Windows longer than 68.7 s are clamped to the longest memory (shown in the text).

**Slow scans / continuous update** (acquisition windows ≥ 1.5 s, the `long_acq` regime of `src/worker.c` in which
the trace is published while it is acquired, see [Slow scans](#slow-scans)):

- armed in Normal on the scan floor, the trace always starts at the floor and **grows to the right**; with a
  triangle it reaches the top at T/2, stays still for the other half period and starts again from the floor;
- the time zoom uses the model of the ramp, not the samples, so it works with an incomplete trace; after a zoom the
  acquisition in progress (old limits) ends and the next one starts at the next floor of the new ramp.

Example (v2.3.31, 0.2 Hz triangle ±4000, T = 5 s): window 0 … 2.5 s (`time_units` s); the last sample of the trace
moved 1.60 → 2.00 → 2.50 s every 0.5 s.

![0.2 Hz triangle: window 0 … 2.5 s (T/2), the trace half drawn while it is acquired (v2.3.31)](.Usage/lock_osc_screen_slow_0.2Hz_rising_half.jpg)

**Turning it off** (`rampLockScreenOff()`, l. 3914):

- unchecking it: the trigger (External / Normal / Scan floor) and the time window **stay as they are**; only the
  normal time zoom of the plot comes back (SHIFT + wheel zooms the view again, without touching the ramp);
- choosing another *Source*, *Ext Trig* or *Mode* in the page (also *Mode* = Single), pressing **AUTO** (`serverAutoScale()`, l. 6670), or
  pressing **Single** (`singleUpdate()`, l. 6163) also turns it off, with the same rule (trigger and window kept, the
  choice of the user applied);
- it is **not saved** in the configs (it is a state of the page: after a reload it is off).

**With Capture Lock** ([Lock Control](#lock-control)): during a capture *Lock osc. screen* is suspended (the
capture uses its own trigger and window; the wheel zoom is only in the page, as for any capture) and when the
capture ends it comes back with its window; ending the capture with **Single** turns it off (above).

The screenshot of the panel before v2.3.31 (v2.3.24, no tabs; `__scan_mode.json`, OscA = Ramp A, OscB = in1, ±5000
counts, period 400, triangle → τ = 64.16 ms, f = 15.59 Hz, the two peaks of in1 seen on the way up and down):

![Ramp Controller panel of v2.3.24 (no tabs)](.Usage/panel_ramp_controller.jpg)

### PIDs modules

![PIDs modules panel](.Usage/panel_pids_error_selector.jpg)

- **Error signal selector**: *Error signal* (0, Xo, Yo, F1o, F2o, F3o, in1, in1−in2) and its *offset*.
- **PID A / PID B**: *input* (error by default), *reset integral*, *freeze out*, *freeze integral*, and
  the gains *kp*, *ki*, *kd* with the effective value written below (kp as a factor, ki and kd as τ and f).
- **More Options** shows the set point *sp*, the scale selectors of kp (/1../4096), ki (8 ns..9 s) and kd
  (7.5 ns..491.5 µs), and *SAT lim* (saturation of the integral term, ±122 µV..±1 V). The ki option 4 is
  labelled "65 us" since v2.3.15 ($2^{13}$ · 8 ns = 65.5 µs; it said "6 us"):

![PID A with ki scale 65 us: ki = −20 gives τ = 3.28 µs](.Usage/panel_pidA_isr_65us.jpg)

![PID A with More Options](.Usage/panel_pidA_more_options.jpg)

In the example (`lock_mode`) kp = −250 with /1024 gives −0.244, and ki = −20 with 537 ms gives τ = 26.8 ms
(f = 37.3 Hz); kd = 0 (OFF), SAT ±1 V.

### Lock Control

![Lock Control panel](.Usage/panel_lock_control.jpg)

The main part of the panel (from top to bottom):

- **Scan enable / PID A enable / PID B enable**: buttons with the **effective** state of the ramp and the
  PIDs (dark = on). When nothing is locked a click toggles the manual enable; while LOCKED a click
  releases the lock keeping the other enables.
- **Trigger Lock**: arms the lock; it closes when the trigger of the *config* section happens (time,
  level or level+time). **Lock Now**: closes the lock at once. Both stay pressed while requested; a second
  click releases the lock.
- **time / level / time+level** (the three small colored buttons between Trigger Lock and Lock Now; since
  v2.3.28): a shortcut for *Trigger type* + *Choose from graph* + *Fire on click*. Click one (it stays filled while
  it waits, the cursor over the plot is a crosshair and a short note covers the state label and the checkboxes
  below), then click on the plot: the trigger type is set, the time
  and / or level are taken from the click, and *Trigger Lock* fires at once (with *Capture Lock* if checked, even if
  *Fire on click* is unchecked). An active lock is kept until that click, then released and armed again. Esc or a
  second click on the same button cancels.
- **State label**: OFF / ARMED / LOCKED and the number of locks since the FPGA was loaded.
- **Capture Lock** (on by default): every lock request from the page captures the closing of the loop in
  the scope and freezes the trace. **Fire on click** (on by default): with *Choose from graph*, a click on
  the plot sets the trigger value and fires *Trigger Lock*. Design: [`lock_capture.md`](../lock_in+pid_harmonic/doc/lock_capture.md).
- **config** (open it with its title):

![Lock Control config](.Usage/panel_lock_control_config.jpg)

  - *Scan enable*, *PID A enable*, *PID B enable*: what is on **while LOCKED** (usually: scan off, PID A on).
  - *Trigger type*: OFF (only Lock Now), Time trigger, Level Trigger, Level+time Trigger.
  - *Time trigger*: delay after the scan floor, in ticks of 8 ns or with units (`16.58 ms`, `20 s`; see
    [below](#typing-values-with-units)); shown as T below (typing `16.58 ms` gives 2072500, T = 16.580 ms, as in
    the screenshot; the test configuration uses 2072622). 0 = OFF, up to 4294967295 =
    34.36 s (32 bits since v2.3.15; it was limited to 17.18 s).
  - *Signal for trigger*, *Level trigger* (counts or `V`/`mV`, shown in mV below), *trig upward?*: for the level trigger.
  - **Choose from graph**: the next click on the plot sets the time (and/or level) of the trigger. A second
    click on the button (*Cancel*) or Esc cancels it. A red warning appears if the scope is not in
    Normal/Single + External + Scan floor (the only setup where t = 0 of the plot is the scan floor).

- **Re-lock system** and **Step Responce Measurement** (open them with their titles):

![Re-lock, step response and Monitor](.Usage/panel_relock_monitor.jpg)

  - Re-lock: *Error Enable* with `|error| >` threshold, *Signal Enable* with a signal `<` threshold,
    *RL reset*. Not tested on this version (see [App.md](App.md#re-lock-and-step-response)).
  - Step response: *Jump ctrl_A*, *Jump ctrl_B*, *Freeze during step* (A/B out, A/B int), *Start Step Responce*.

How the lock control works inside: [`lock_control.md`](../lock_in+pid_harmonic/doc/lock_control.md).

### Streaming

See the Outputs screenshot above.

- **IP** (the *IP* button fills in the address of the computer running the browser), **Port** (6000 for
  the server of `resources/streaming`), **Streaming Rate** (1.95 MS/s .. 1.9 kS/s; 0.98 MS/s is the fastest
  continuous rate).
- **Prepare Streaming** starts `c/streaming` on the board; **Start** / **Stop** send the data.
- Start the receiver on the computer first (`resources/streaming/server`, or `nc -l <port>`); details in
  `resources/README.md`.

### Right panels and displays

![Harmonic Lock-in display and Monitor, with the loop closed](.Usage/panel_harmonic_lockin_display_locked.jpg)

- **Trigger**: *Source* (Channel 1, Channel 2, External), *Mode* (Auto, Normal, Single), *Edge*, *Level* (in V, or in
  ADC counts in Raw Mode, −8192 … 8191, since v2.3.29), and the *Single* button. External uses the *Ext Trig* of the Oscilloscope panel.
  **Auto** (since v2.3.26) waits for the trigger as *Normal* does (the *Level* of the source channel, or the
  *Ext Trig* with Source = External) and forces an acquisition only when no trigger comes within a time limit:
  the largest of 0.25 s, 1.1 × the window + 50 ms and, when the period of the Ext Trig is known (Scan floor /
  Scan ceil with the scan running, harmonic mod.), 1.1 × that period + 50 ms; at most 80 s. So with Ext Trig = Scan
  floor, t = 0 is the scan floor in Auto too (a 30 s scan in a 0…29.4 s window waits up to 33 s and every scan is
  acquired from its floor), and without a trigger (scan stopped or locked with the ramp off, Ext Trig None, a level
  the signal never crosses) the traces keep coming: every 0.25 s plus the acquisition for short windows. As before,
  an Auto acquisition starts at the trigger (no negative times). Up to v2.3.25 Auto triggered at once, at any phase
  of the scan (Scan floor seemed to trigger at the ceiling). The *Level* field and line work in Auto too.
- **Range**: buttons for the X and Y scales and offsets.
- **Measure**: min, max, amplitude, average, frequency and period of each channel.
- **Gain settings**: probe attenuation (1x/10x) and LV/HV jumper setting of each input (scale of the display).
- **Harmonic Lock-in** (below the plot): X, Y, R, φ, F1, F2, F3 in volts.
- **Monitor**: mean and standard deviation of the error over ~1 s, in counts.

In the screenshot the loop is closed (LOCKED, Mode Auto), so X, Y, R, φ and the Monitor are steady (error std
26.87 counts). During a scan these values change all the time and a reading is only an instant of the sweep.

### Slow scans

With windows of 1.5 s or more (e.g. a 30 s ramp) the scope reads its memory while the FPGA is still writing it.
Since v2.3.23 (CHANGELOG v2.3.23):

- **Reset zoom** on a scan of period T ≥ 1.5 s (Ext Trig = Scan floor / Scan ceil / harmonic mod.) sets the window
  to 0 … 0.98 × T (at least 50 ms before the next trigger), so that the scope is armed again in time and every scan
  is acquired. Shorter periods keep one whole period. The rising half of a triangle (second click with Scan floor,
  v2.3.31) is 0 … T/2: it already ends half a period before the next floor, so no 0.98.
- **Lock osc. screen** (v2.3.31) uses 0 … T/2 with a triangle and the same window as Reset zoom (0 … 0.98 × T) with a
  sawtooth, and keeps it when the ramp changes; its time zoom works on an incomplete trace
  ([Lock osc. screen](#lock-osc-screen)).
- The trace is drawn **while it is acquired**, only with valid points of the current acquisition (it starts and
  ends at the valid ones, never mixed with an older lap of the memory, and the previous trace is not left to the
  right). In Normal mode the **whole trace is only seen near the end of each scan**: between the end of the
  window (0.98 × T) and the next scan floor.
- **Capture Lock** works with slow scans (Time trigger, Level trigger and Lock Now): the lock request is held until
  the scope has loaded its **history before the lock** (the part of the window before t = 0; banner "loading the
  scope history before the lock (x s)"), then the lock is applied and the capture is drawn as it is acquired
  ("lock captured, acquiring the trace..."). Lock Now on a slow window therefore locks after that history (e.g.
  9 s for a 30 s window), on purpose.
- (FPGA) A time trigger armed after the ramp was stopped (e.g. right after releasing a lock) waits for the next
  scan floor instead of firing in the middle of the scan.

![Slow scan: 30 s triangle, Reset zoom 0 … 29.4 s (0.98 × T), whole trace](.Usage/slow_scan_30s.jpg)

In the screenshot: `lock_mode` with *Ramp period* 187499 (τ = 30.00 s, f = 33.33 mHz), ±5000, Trigger External /
Normal / Scan floor, Reset zoom → 0 … 29.4 s; ctrl_A and error complete up to 29.45 s (1024 points), with the
zero crossings of the error at ≈ 7.8 s and ≈ 22.3 s.

## Typing values with units

Since v2.3.16 the **Time trigger** and **Level trigger** fields of *Lock Control → config* are text fields that
accept a number with a unit (`index.html` l. 2433-2464: `parseTrigTime()`, `parseTrigLevel()`, `input_unit_parsers`):

| Field | Without unit | Units | Range | Examples |
|---|---|---|---|---|
| Time trigger | ticks of 8 ns | `s` (`seg`), `ms`, `us` (`µs`), `ns`, `tick(s)` | 0 .. 4294967295 (34.36 s); larger values are clamped; a nonzero time below one tick is 1 tick | `16.58 ms` → 2072500, `20 s` → 2500000000, `16,58ms` → 2072500 |
| Level trigger | counts | `V`, `mV`, `count(s)` | −8192 .. 8191 (clamped) | `0.1 V` → 819, `-50 mV` → −410 |

- Decimal point or comma; the space between number and unit is optional; units are not case sensitive.
- The value is sent when the edit ends (Enter or leaving the field); then the field is rewritten in ticks /
  counts and T / V_trg below it are updated. Escape restores the previous value.
- An empty or invalid text (`abc`, `-5 ms`) is not sent: a red hint appears below the field and the last value
  comes back. The mouse wheel changes the value by one tick / count.
- Values above $2^{24}$ ticks (134 ms) go through the float parameters of the C controller and are rounded to a
  multiple of 2 to 256 ticks (e.g. `19 s` = 2375000000 is written as 2375000064, 0.5 µs more); see
  [FPGA.md](FPGA.md#lock-control-auto-lock).

Tested on the board (v2.3.16): `20 s`, a pasted `19 s`, `16.58 ms`, `16,58ms`, empty / `abc` / `-5 ms` (nothing
sent), `0` (OFF), `40 s` (→ 4294967295), wheel, Escape; `0.1 V`, `-50 mV`, empty (`reportes/lock-in_pid_h.md`).

![Time trigger typed as "20 s"](.Usage/time_trigger_units_20s.png) ![Time trigger "40 s", clamped to 34.36 s](.Usage/time_trigger_max_34s.png)

Since v2.3.31 **Ramp period** (tab *period* of the Ramp Controller) is also a text field with units: steps, or the
whole period of the ramp in `s`, `seg`, `ms`, `us` (`rampStepParseField()` in `input_unit_parsers`), sent with Enter or
when leaving the field and rewritten in steps ([Tabs period and freq](#tabs-period-and-freq)). The fields of the
*freq* tab accept units too (*Frequency* in Hz / kHz / mHz…, *Amp. p-p* and *Offset* in counts or `mV` / `V`).

Other fields still have older unit conversions in the JavaScript, but they are `<input type="number">` fields: the
browser does not give a text with letters to the page (`.val()` is empty), so those conversions can not be reached from
the UI (the same was found for *Ramp period* in `lock_in+pid_plus` 2.2.0-rc2, CHANGELOG v2.3.31):

| Field | Conversion in the code | Usable from the page |
|---|---|---|
| Ramp hig / low lim | `V`, `mV` → counts (`lock_ramp_step_update()`, l. 2020-2036) | no (use *Amp. p-p* / *Offset* of the *freq* tab) |
| PID A / B sp | `V`, `mV` → counts (l. 2149-2152, 2256-2259) | no (not tested on the board) |
| Period of the harmonic oscillator | `s`, `seg`, `ms`, `us` → `gen_mod_hp` (`lock_modulation_update()`, l. 2359-2364) | no |
| Phase of the harmonic oscillator | `deg` / `g` / `°`, `rad`, `pi` → counts (l. 2347-2352) | no |

## Procedures

These procedures follow `test_files/lock_test.md`, the procedure used to test every version on the board.
The example numbers are those of the test configurations `test_files/lock_in+pid_harmonic__scan_mode.json`
and `__lock_mode.json`: a system with a resonance (a peak) whose control input is OUT1 and whose response is
measured on IN1.

### 1. Scan and see the response of the system

1. **Outputs**: Out1 = `ctrl_A`.
2. **Ramp Controller**: limits ±5000 (±610 mV), period 400 (triangle: 64.16 ms), *Scan enable* checked.
3. **Lock Control**: *Scan enable* button on, *PID A enable* off.
4. **Oscilloscope**: OscA = `Ramp A` (or `ctrl_A`), OscB = `in1`; Ext Trig = *Scan floor*.
5. **Trigger**: Source *External*, Mode *Normal* (picking an Ext Trig already sets them, v2.3.24). Press
   **Reset zoom**: the window goes from 0 to one period of the ramp (0 … 64.16 ms) and t = 0 is the scan floor.
   The preset `in1|ctrl` sets the same pair in one click (with in1 on Channel 1 and ctrl_A on Channel 2).

The response of the system (the peak) appears on Channel 2 at the same position in every sweep.

Alternatives since v2.3.31: in step 2 use the **freq** tab (e.g. Frequency `15.59 Hz`, Amp. p-p 10000, Offset 0), or
type `64.16 ms` in *Ramp period* (gives step 400); and instead of step 5 check **Lock osc. screen**, which sets the
trigger and the window of the rising half of the triangle (0 … 32.08 ms: each peak of the response appears once) in
one click. Then a **box selection** (or SHIFT + wheel) around the peak narrows the scan to that zone at the same
frequency: the peak gets wider on the screen, which is a quick way to find the limits of a scan for the lock
([Lock osc. screen](#lock-osc-screen)). Without Lock osc. screen, a second click of *Reset zoom* also shows the rising
half ([Reset zoom](#reset-zoom-whole-period--rising-half)).

### 2. Configure the lock-in to get an error signal

The lock-in, with a small modulation added to the control signal, gives a signal proportional to the
derivative of the response with respect to the scan: it crosses zero at the maximum of the peak, which is
the error signal for the PID.

1. **Lock-in modules**: Lock-in input = `in1`; Period = 0 (49.6 kHz); *A Out1* = 100 (modulation of ≈ 6 mV
   added to OUT1); X & Y filter 262 µs | 607 Hz, order 2; Amplification ×32.
2. Look at `Xo` and `Yo` (OscA/OscB) during the scan: change the *Phase* of the references or choose the
   component (X or Y) that gives a clean dispersive curve with a zero crossing at the peak.
3. **PIDs modules**: Error signal = that component (`Yo` in the test configuration), offset 0.
4. OscA = `ctrl_A`, OscB = `error` (preset `ctrl|err`):

![Scan: ctrl_A and error](.Usage/scan_mode_peak_normal_scan_floor.jpg)

### 3. Close the lock

1. **PID A**: input = error, kp = −250 (/1024, −0.244), ki = −20 (537 ms, τ = 26.8 ms). The sign of the gains has to give
   negative feedback around the zero crossing (try the other sign if the lock runs away).
2. **Lock Control → config**: while locked, *PID A enable* on and *Scan enable* off.
3. Choose the trigger:
   - **Time trigger**: press *Choose from graph* and click on the zero crossing of the error (16.58 ms in
     the example). With *Fire on click* on, the click also fires *Trigger Lock*.
   - Shortcut: press the small **time** (or **level**, **time+level**) button between *Trigger Lock* and
     *Lock Now* and click on the plot: type, value and *Trigger Lock* in one go (steps 3 and 4).
   - **Level trigger**: Signal for trigger = error, Level = a value the error reaches just before the
     crossing (5085 counts, V_trg = 621 mV, in the test), *trig upward?* according to the slope.
   - **Lock Now**: locks immediately wherever the ramp is (useful only when the system is already near the
     point).
4. Press **Trigger Lock**. The state goes OFF → ARMED → LOCKED in the next sweep; with *Capture Lock* the
   scope shows the closing of the loop (t = 0 is the lock) and keeps it frozen:

![Lock captured with the time trigger](.Usage/capture_lock_time_trigger.jpg)

With the level trigger the lock is placed at 30 % of the window:

![Lock captured with the level trigger](.Usage/capture_lock_level_trigger.jpg)

Fire on click on a frozen capture moves the lock point and locks again (GIF):

![Fire on click](.Usage/fire_on_click.gif)

If *Choose from graph* shows the red warning, t = 0 of the plot is not the scan floor and the time taken
from the click would be wrong:

![Choose from graph warning](.Usage/choose_from_graph_warning.jpg)

The frozen capture ends (and the scope settings saved before the capture are restored) with trigger mode
Auto/Normal, *Single*, **AUTO**, a change of source or Ext Trig, unchecking *Capture Lock*, or a release
while waiting. *Autoscale* keeps it.

### 4. Check the lock and release it

1. Set the trigger Mode to **Auto**: the ramp has stopped and the error stays at 0 (OscA = `ctrl_A`,
   OscB = `error`):

![Locked: ctrl_A and error](.Usage/locked_auto_ctrlA_error.jpg)

2. With OscA = `in1` (preset `in1|err`) the signal stays at the top of the peak (1.01–1.03 × the peak in the tests):

![Locked: in1 and error](.Usage/locked_auto_in1_error.jpg)

3. The **Monitor** panel shows the mean (≈ 0) and the std of the error: ≈ 27 counts ≈ 3.3 mV with kp = −250
   (26.85 counts in the [screenshot](#lock-control) of the Monitor; `test_files/lock_test.md`). With the kp = −500 of
   the configurations before 2026-10-12 it was ≈ 60 counts ≈ 7–8 mV.
4. **Release**: a second click on *Trigger Lock* (or *Lock Now*), or a click on *Scan enable* (restarts the
   scan with the PIDs as they were).

A lock can also be closed and checked without the web page, with `py/lock_from_registers.py` on the board
or over HTTP (see [Remote.md](Remote.md)); the page follows the state without sending anything.

## Saving and loading configurations

**Config** opens the configuration dialog:

![Configuration dialog](.Usage/config_modal.jpg)

- *Save in browser* stores all the parameters (and the Capture Lock / Fire on click preferences) under the
  *Config Name* in the browser (`localStorage`, key specific of this App). *Save as file* downloads a JSON.
- The list shows the saved configs with *del*, *download* and *load*. *Load file* adds a JSON file to the list
  (then press its *load*).
- **Don't turn on PIDs and Ramp on config loading**: **unchecked by default** (since v2.3.26; up to 2.3.25 it was
  checked). Unchecked, *load* (also of a *Load file*) sets the ramp (*Scan enable* and the Lock Control ramp
  enable) and the PIDs as they are in the config: a config saved while scanning loads scanning. Checked, a loaded
  config never turns them on (useful when the outputs are connected to an experiment). The same option applies to
  the restore of the last config / tab state after a start / *Restart*. A lock request (*Lock Now*, *Trigger Lock*) is never
  loaded. The option is not saved: every page load starts with it unchecked.
- Configs are per browser, not stored on the board.
- **Load last config on init** (since v2.3.27): **checked by default**; the choice is kept in the browser
  (`localStorage`, key of this App). The page saves the current settings automatically every ~2 s (the *last
  config*, also in `localStorage`). Checked, each time the page starts the App (main menu, new tab, F5) it restores
  the last config; unchecked, the App starts with its defaults. The ramp / PIDs of the restored config follow the
  option above; a lock request is never restored.
- **Load last config** / **Reset to defaults** (since v2.3.27): close the dialog and restart the App (the page reloads,
  the FPGA is reloaded: outputs and lock are reset) with the last config / with the default parameters of the App (as
  a fresh start: lock open, ramp stopped, PID gains 0), whatever the checkbox says. After *Reset to defaults* (or an
  open with the box unchecked) the last config is kept until a parameter is changed, so *Load last config* brings it
  back.
- **Time window** (v2.3.17): *load* applies the time window of the config in the units it was saved with.
  The config keeps `xmin`/`xmax` in the time units of the moment it was saved (µs, ms or s); the page converts
  them to seconds, sets the window in the current units and then takes the window and units that the server
  ends with (the answer of the last of the 5-9 POSTs of a load), so page, axes and server agree. The scale values
  that the server derives (`time_units`, `time_range`, `gui_xmin`, `gui_xmax`, `forcex_flag`) are not loaded nor
  sent. Up to v2.3.16 the window was taken in the units of the server (`lock_mode`, saved in ms, loaded with the
  scope in µs gave −2…33 **µs**) or not applied at all. Tested on the board: 14/14 loads (from 0-131 µs,
  10-120 µs, 0-10 ms, 0-2 s, and a config in µs loaded with the page in ms).
- A load ends a frozen lock capture (the config brings its own scope settings).
- *Lock osc. screen* and the active tab of the Ramp Controller are not saved in the configs (v2.3.31). A load changes
  the ramp, so with *Lock osc. screen* on the window follows it.

![lock_mode loaded with the scope in µs: window −2.07…33.49 ms (v2.3.17)](.Usage/config_load_lock_mode_window.jpg)

## Saving data

*Save Data* gives the data of the plot as Python/Numpy vectors, Matlab/Octave vectors or CSV (save as a
file, copy or show).

## Several clients and Restart

Only one browser tab should control the board. When another client (another tab, the main menu, another
App) takes the board, the page stops polling and shows a dialog:

![Another client took control](.Usage/restart_modal.jpg)

*Restart* restarts the App and restores the state of this tab (if the other client loaded the same App,
the FPGA is not reloaded), with *Load last config on init* checked or not. On Ecosystem 2.0 the page also enters a "cautious mode" when the board answers
slowly, and waits until it answers fast again.

## Known limitations of the interface

- The **Slow outputs** selectors have no effect; the **R|Phase Mode** button is disabled.
- *Time trigger* values above $2^{24}$ ticks (134 ms) set from the page are rounded to the float32 grid (≤ 1 µs).
- *Ramp hig lim* / *Ramp low lim* (tab *period*) do not accept `mV` / `V`: they are `<input type="number">` fields
  ([Typing values with units](#typing-values-with-units)); use *Amp. p-p* / *Offset* of the *freq* tab.
- The mouse wheel over *Ramp period* does not move the step above $2^{24}$ (16777216 steps; with N = 16000 a period of
  ≈ 2147 s): the parameter travels as a float32, and ±1 rounds back to the same value (granularity 2 … 128 there). At
  the maximum 2147483520, wheel −1 sends 2147483519 and 2147483520 comes back (seen on `lock_in+pid_plus` 2.2.0-rc2,
  same code). Typing a value or a period works. (The wheel of the *freq* tab already moves to the next float32 step.)
- After a **reload of the page with a slow scan running** (windows ≥ 1.5 s, continuous update), the X axis follows the
  trace while it grows (0 … 0.2 → 0 … 4.2 s) instead of staying on the window; *Reset zoom* fixes it (seen on
  `lock_in+pid_plus` 2.2.0-rc2; probably older than the Ramp Controller).
- `loadParams()` keeps the window of the plot in the parameters only when its minimum is not 0
  (`if(options.xaxes[0].min && options.xaxes[0].max)`, `index.html` l. 5404): with a window that starts at t = 0 the
  parameters take the `xmin` / `xmax` of the server instead of those of the plot. Up to v2.3.30 this let a repeated
  *Force X* undo a wheel / box zoom made from t = 0 before its POST; since v2.3.31 the *Force X* is filtered
  ([Structure.md](Structure.md#time-window-of-the-plot-and-force-x)), but the rule of `loadParams()` is unchanged
  (pending for devAgent).
- The labels of *Signal for trigger* 6-8 show code text (`/*sqXo */ 14'b0`): those options are 0.
- Each change made in the page is a `POST /data`, and on Ecosystem 2.0 each one leaves an open connection in the
  nginx of the board; after ~1000 the board stops answering until nginx is restarted
  ([Remote.md](Remote.md#known-issue-of-the-ecosystem-post-data-leaves-connections-open)).
- Level+time with the time after the level crossing stays ARMED (the level crossing has to happen after
  the time).

These items are listed for devAgent in `docAgent.md`.
