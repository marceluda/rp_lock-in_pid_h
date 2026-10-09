
# Devbuild  changes


v0.3.1
- FIXED bug on PID derivative constant label

v0.3.2
- ADDED long time-range signal storing (by local script)

v0.3.3
- ADDED digital pin for ramp_scan externa synchronization

v0.3.4
- ADDED Sawtooth waveform for Ramp intrument
- ADDED larger decimation for Scope instrument: up to 64 seconds time range

v0.3.8
- Better remote control
- ADDED server restart function
- ADDED some HTML interface features

v0.3.9
- ADDED support for ecosystem 2.0 of RedPitaya

v0.3.10
- FIXED "Error while sending data (E3)" on ecosystem 2.0: only changed parameters are sent,
  in sequential POSTs of at most 600 B, with retries; only finite numeric values are sent
- FIXED nginx worker segfault on ecosystem 2.0: the loaded App is probed with an empty POST
  before polling /data
- ADDED detection of another client (e.g. main menu) taking control of the board, with
  Restart and restore of the user state
- FIXED robust App start on ecosystem 2.0 (stop previous App, wait, start, verify, retry)
- FIXED "Don't turn on PIDs and Ramp" now also disables Scan enable and lock triggers
- FIXED Config load / Load file failing with missing read-only keys (lock_X, lock_Y, ...)
- FIXED saved configs stored under an App-specific localStorage key
- FIXED reload_fpga does not touch the FPGA on ecosystem 2.0 (returns 501)
- FIXED index.html served with Cache-Control: no-cache
- FIXED month value in pretty_now() and GUI xmin/xmax read by index in main.c
- FIXED Makefile packaging of fpga.sh / fpga.bit.bin and fpga.sh executable mode

---

# devel2.0 branch (Ecosystem 2.0, FPGA built with Vivado 2020.1)

Versions 2.3.x are the same App as the 0.3.x series, rebuilt for the Red Pitaya Ecosystem 2.0 with the FPGA
design ported to Vivado 2020.1 (RedPitaya-FPGA project structure, v0.94, model Z10 / STEMlab 125-14).
Every version below was tested on a board (RP OS 2.04-35) with the LOCK MODE procedure, locking to a peak
simulated by `dummy_simulator` on a second board. Lock metrics were identical in all of them: lock in
< 50 ms, IN1 at 1.01-1.03 x the peak, error std ~7-8 mV.

## v2.3.14 - Capture Lock and Fire on click

### Added
- **"Capture Lock"** checkbox (on by default). Every lock request from the page (Trigger Lock, Lock Now,
  Fire on click) captures the closing of the loop like a Single acquisition: the scope goes to Single +
  External + Ext Trig = "Lock control trig" (the FPGA pulse emitted when the lock closes) and the lock
  request is written only once the scope is armed. Captured 16/16 times on the board (before, only when
  the Normal scope happened to be armed at the right sweep, ~60 %).
  The trace stays frozen ("Lock captured - press Auto or Single to refresh") until AUTO, trigger mode
  Auto/Normal, Single, a source / Ext Trig change or unchecking the box; then the user scope settings are
  restored. The "Autoscale" button (Y axis only) keeps the capture.
  Design notes: `lock_in+pid_harmonic/doc/lock_capture.md`.
- **"Fire on click"** checkbox (on by default): a click with "Choose from graph" sets the time / level and
  fires Trigger Lock at once (an active lock is released and armed again with the new value).
- Simulations: `test/lock_capture_ui_sim.js` (UI + controller + scope + lock) and `test/auto_set_c_sim/`
  (the real C controller compiled for the PC).

### Changed
- "Choose from graph": the warning about the scope trigger is recomputed whenever the scope or lock trigger
  settings change; Esc or a second click ("Cancel") cancels a pending click.
- `py/lock_from_registers.py`: does nothing if the lock is already LOCKED / ARMED with the same request
  (it used to open the loop for some ms); `--force` re-arms.

### Fixed
- Every POST reset the scope, so any change (a PID gain, a lock request) disarmed a Single waiting for its
  trigger. A POST without scope changes no longer touches the scope.
- AUTO after a lock capture left Ext Trig on "Lock control trig", and the lock / PID / generator values
  sent with AUTO were dropped. The auto-set now starts from the current parameters and only copies back
  the scope values it computes; an aborted auto-set no longer restarts itself (10 s wait).
- A zoom-out of more than 33x right after a change of time units was ignored.
- Packages no longer include `py/__pycache__` / `*.pyc`.

## v2.3.13 - The lock no longer depends on the web UI

### Changed
- **The lock sequence runs entirely in the FPGA** (`lock_ctrl.v`, state machine OFF / ARMED / LOCKED).
  `lock_control` (0x18) is now command + configuration and is never modified by the FPGA nor rewritten
  from its state. Same bit layout: `[0]` lock now and `[1]` launch lock are requests (0->1 edge locks /
  arms, `[1:0] = 00` releases), `[4:2]` manual enables, `[7:5]` enables when locked, `[9:8]` trigger type,
  `[10]` level direction. Changing a manual enable while locked releases the lock.
  Design notes: `lock_in+pid_harmonic/doc/lock_control.md`.
- **Register 0x1C is now `lock_status` (read only)**, replacing `lock_feedback`: `[0]` armed, `[1]` locked,
  `[4:2]` effective ramp / PID A / PID B enables, `[15:8]` lock counter. No other register moved.
- C controller: `lock_lock_status` replaces `lock_lock_feedback`; `lock_control` is written only when the
  user changes it, and the status (also of a lock started from outside, e.g. Python) is read on every
  request.
- Web UI: Scan / PID A / PID B show the effective enables, plus an OFF / ARMED / LOCKED label with the lock
  count. Trigger Lock / Lock Now stay pressed while requested; a second click releases the lock.
- `resources/config_tool.py` updated for the v0.94 FPGA tree.

### Added
- `py/lock_from_registers.py`: arm, lock now, release and read the status writing only FPGA registers
  (no web UI needed).
- xsim testbench of `lock_ctrl` and a node simulation of UI <-> controller <-> FPGA in `test/`.

### Fixed
- The lock was only "committed" after the web UI copied `lock_feedback` back to `lock_control`; with the
  scope not triggering, the UI showed a wrong state. No POST is sent while locked.
- `resources/remote_control/.../control_hugo.py`: `launch_lock()` / `lock_now()` always failed; added
  `release_lock()` and `lock_status()`.

## v2.3.12 - "Choose from graph" fixed

### Fixed
- **The time picked with "Choose from graph" was wrong in some views.** It is now correct with any zoom,
  offset and time units, with t = 0 on screen or not: it uses the time units of the plotted data (a zoom
  that changes units updated them before the new data arrived) and the real ramp period (the sawtooth
  ramp used the triangle period, so a click outside the first period gave a time never reached).
- A click set both the time and the level trigger; it now sets only the value of the selected trigger type
  (Time, Level, or both for Level+time).

### Removed
- The "Auto-zoom" option (a workaround that moved the zoom to show t = 0). Instead, a warning appears when
  the scope trigger is not Normal/Single + External + Scan floor (the only setup where t = 0 is the scan floor).

### Added
- `test/trig_from_graph_sim.js`: simulation of the click -> time conversion.

## v2.3.11 - Web interface fixes (same as v0.3.11)

### Fixed
- The second of two quick changes was lost while a POST was in flight; Config load during a POST is sent too.
- Indicators (R, X, Y, phase, scope) froze after editing a field; Escape cancels an edit.
- Enter with an out-of-range value sent two POSTs.
- The mouse wheel stopped the scope (it sent Single) and SHIFT + wheel used the wrong sign; a focused field
  sent each wheel step twice.
- **Endless POST loop** (~15 POST/s, it crashed the nginx web server) after loading a config with missing
  keys (e.g. from another App): missing keys keep their value, NaN is never sent, and an anti-loop guard
  limits POSTs.

### Added
- "Cautious mode" on Ecosystem 2.0: if the board answers slowly or another client may be taking it, data is
  not requested until it answers fast again (needs two slow answers in a row; slow answers during our own
  POST are ignored).

## v2.3.10 - FPGA rebuilt with Vivado 2020.1

### Changed
- `lock_in+pid_harmonic/fpga` is now the RedPitaya-FPGA v0.94 project with the lock module. `make` builds
  `red_pitaya.bit` and `fpga.bit.bin`, `make project` opens the Vivado project, `make clean` cleans; Vivado
  2020.1 is loaded inside the Makefile, isolated from the Vivado 2015.2 + Linaro setup of the C controller.
  The 2015.2 design is kept untracked in `fpga_old_2015.2/` (remains in history at v0.3.10).
- The scope is the Red Pitaya 2.0 one: the controller unlocks its trigger (0x94) before each acquisition and
  detects the end of acquisition with conf bit 4 (still works with the 0.9x scope).
- Scope decimation widened to 20 bits in our copy of the FPGA, so the longest time range is again ~68 s
  (decimation 512k, as in v0.3.4).
- The `c/` tools are built by the App Makefile (`make c_tools`) with the flags of the original binaries.
- Kept from the 2015.2 design: lock at 0x40600000, scope at 0x40100000 with the lock signals and lock trigger,
  slow outputs (PWM) driven by the lock, modulation / ramp direction on `exp_n_io[7:6]`, ASG / PID regions
  answer without error.

### Fixed
- Negative scope samples were shown as -1 V (the 2.0 scope returns 16-bit sign-extended samples).
- **Streaming duplicated data:** the scope read data crossed clock domains unsynchronized (FPGA fix in
  `rp_scope_cfg`); the streamer now uses a monotonic write pointer and counts overruns / lost samples.
- Streaming stopped after a few seconds (buffer overflow in `c/stream_tcp_osc_cmd`), the first Start sent no
  data, the end of each streaming was corrupted, and `c/streaming` used 100 % CPU while waiting.
- Error E3 while streaming (the nginx worker blocked waiting for the streaming process); the status label
  flickered.
- Leaving the App with streaming active could read the FPGA while it was reprogrammed (board reboot by
  watchdog): streaming processes are now stopped on App exit and before loading the FPGA.
- Restart after a streaming left the scope frozen and the streaming IP changed (saved as float); transient
  commands are never saved.
- Streaming IPs with the last number >= 128 were rejected; `/lock?name` without `=` gave an error 500.
- A Single click during another POST was lost; the time scale was not restored after Restart.

### Notes
- Decimation 64 (1.95 MS/s) streaming loses ~17 % of the samples (bus limit); decimation >= 128 is sustainable.
- The slow analog outputs AO0-AO3 are not driven by the lock module and `exp_n_io[7]` is always 0, as in the
  2015.2 design.
- FPGA timing does not close (WNS about -10 ns), as in the 2015.2 design.
