
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

v0.3.11
- Web interface fixes ported from rp_lock-in_pid_h_hf v0.3.8
  - FIXED second of two quick consecutive changes being lost while a POST was in flight
    (unsent changes are kept when a POST/GET answer is loaded; Config load during a POST is sent too)
  - FIXED indicators (R, X, Y, phase, scope) frozen after editing a field (edit timer / edit mode);
    Escape cancels the edit; leaving a select or checkbox ends the edit mode
  - FIXED Enter with an out-of-range value sending two POSTs (Enter is prevented, forms use novalidate)
  - FIXED mouse wheel: no longer sends single_btn (scope stopped), and SHIFT + wheel uses the right sign
  - FIXED duplicated POST when using the mouse wheel on a focused field
- Ported from rp_lock-in_pid_h2 v0.4.1 (via rp_lock-in_pid_h_hf v0.3.8)
  - Restart after "took control" restores the saved values when the intruder is the same App
  - ADDED cautious mode: if /get_client_id is slow or fails, /data is not requested until the board answers fast again
- FIXED cautious mode entered without reason during active use: a single slow/failed /get_client_id is retried at once
  (cautious only if the retry is slow/fails too), a slow answer overlapping our own POST /data is not measured, and the
  checks to leave it are 1 s apart (was 3 s)
- FIXED endless POST loop (~15 POST/s, it crashed the nginx worker) after Config -> load of a config without some
  keys (e.g. of another App): missing keys keep their current value, a select without selection never gives NaN,
  NaN is never a pending change, and sendParams() has an anti-loop guard (no POST without changes < 200 ms after the
  previous one, at most 10 POST/s)
  (v0.3.11 is the base of v2.3.11, see below; tag `v0.3.11` on `master`)

---

# devel2.0 branch (Ecosystem 2.0, FPGA built with Vivado 2020.1)

Versions 2.3.x are the same App as the 0.3.x series, rebuilt for the Red Pitaya Ecosystem 2.0 with the FPGA
design ported to Vivado 2020.1 (RedPitaya-FPGA project structure, v0.94, model Z10 / STEMlab 125-14).
Every version below was tested on a board (RP OS 2.04-35) with the LOCK MODE procedure, locking to a peak
simulated by `dummy_simulator` on a second board. Lock metrics were identical in all of them: lock in
< 50 ms, IN1 at 1.01-1.03 x the peak, error std ~7-8 mV.

## Documentation (after v2.3.17, not a new version)

### Changed
- `doc/` and README updated to v2.3.17: `Remote.md` (acquisitions through `/osc` with `TrgUnlock`, the scope
  of the C controller and `POST /data`, the CLOSE-WAIT issue of the Ecosystem, `control_finn.py` API and the
  `POST /data` made by each function), `FPGA.md` (ranges and widths of v2.3.15, 32-bit `lock_trig_time` and
  float32 rounding of the page, `TrgUnlock`, bus reads of v2.3.17), `Usage.md` (Time / Level trigger fields
  with units, empty fields, Config -> load time window, ki "65 us"), `App.md`, `Structure.md`, `Devel.md`
  (tests, upload targets, timing); references to lines of `lock.v` updated to v2.3.17.

## v2.3.17 - Bus reads of in1/oscA, Config load time window, host name resolved once

### Fixed
- **Corrupt bus reads of fast signals (FPGA, preexisting).** About 2-3 % of the reads of `in1`
  (0x406000D4) and of `oscA` showing `in1` (0xE4) returned 32 bits of garbage (e.g. `0x0118c9c1`) when `in1`
  changed sign between clocks (lock mode, ramp); found by testAgent, also with the FPGA of v2.3.14. Cause: the
  PS side of the bus (`sys_bus_cdc`, clock `fclk[0]`) takes `sys_rdata` some cycles after `sys_ack`,
  asynchronously to the ADC clock, and `lock.v` reloaded `sys_rdata` on every ADC clock with the live value,
  so the PS could take a mix of the bits of two values. Now `sys_rdata` only changes while a read is requested
  (`sys_ren`) and then holds its value (the same fix the scope got in v2.3.10). The read-only wires (`in1`,
  `in2`, `out1`, `out2`, `oscA`, `oscB`, `pidA_in/out`, `pidB_in/out`, `ramp_A/B`, `sin_ref`..`cos_3f`,
  `error_mean/std`, `lock_status`) are read from registered copies held during the read (the value read is
  the one of the clock before the request; one more clock of latency, bus reads only, the loop does not use
  them), the `read_ctrl[0]` copies are also held during the read, and a 2-cycle multicycle constraint covers
  the read multiplexer. Worst path to `sys_rdata`: -10.035 ns (34 logic levels from the PID) -> +1.892 ns;
  `in1` -> its copy +3.7 ns. Design WNS -10.035 -> -8.954 ns; TNS -8637 -> -9565 ns (new copies of
  `out1`/`out2`/`pidX_in`/`pidX_out`, which carry the long paths of the loop: -462 ns; the rest is place and
  route variation, mostly the reset net of the scope). New FPGA image.
- **Config -> load applied the time window in the units of the server** (since v2.3.12): `xmin`/`xmax` of a
  config are in the time units of the moment it was saved, but the server reads them in the units it uses
  now (`time_units` is read-only and follows the decimation), so the `lock_mode` config (ms) loaded with the
  scope in us gave -2...33 us; with a window not starting at 0 the config window was not applied at all
  (`loadParams()` keeps the plot window). The window is converted to seconds and applied in the current
  units after loading (as the restore after a restart does); the server answers with forceX if the units
  change. `time_units`, `time_range`, `gui_xmin`, `gui_xmax` of a config are no longer loaded.
  Build 35 (found on the board in build 34, about half of the loads): the config is sent in several POSTs, and a
  later one carried the stale `forcex_flag` 0 (and `time_units`, `time_range`, `gui_xmin/xmax`) of the page, which
  ended the forceX of the new window; as the page does not load the answers during a config load, it kept the
  window in the old units (`lock_mode` shown as -2069.69...33485.87 ms; also axes 0...0.131 for a config in us
  loaded with the page in ms). These five values are no longer sent by a Config -> load, and the window and
  units the server ends with (answer of the last POST) are applied to the page and the plot axes.
- `example_usage.py`: the Ramp cell (`step=100`, +-4000: 12.9 ms period) was faster than the 16.58 ms time
  trigger of the Lock cell, which never locked (ARMED, timeout). It now uses the ramp of the `lock_mode` config
  (`step=400`, +-5000, ~64 ms), with a note that a smaller `ramp_step` is a faster ramp.

### Changed
- `control_finn.py`: the host name of the URL (e.g. `rp-XXXXXX.local`) is resolved **once**, when
  `RedPitayaApp` (or a standalone `Lock` / `Osc`) is created, and every request (GET and the one-send POST
  /data) goes to that IP with the original name in the `Host:` header. On the PC a `getaddrinfo()` of the
  `.local` name took 3.5 s some times, and `requests` resolved it in every request. `rp.ip`, `rp.resolve()`
  (resolve again, e.g. after a DHCP change), `RedPitayaApp(url, resolve=False)` (old behaviour). IPv4 first;
  IPv6 only if not link-local; if the name does not resolve, a warning and the name is used as before.

### Added
- `test/lock_bus_read_sim.sh` + `test/lock_bus_read_tb.sv` (xsim): `lock.v` reads through `sys_bus_cdc`
  with asynchronous clocks; checks that `sys_rdata` is stable when the PS takes it (2000 reads of `in1` and of
  `oscA` changing sign every clock: v2.3.16 2000/2000 unstable, v2.3.17 0).
- `test/config_load_window_sim.js`: Config -> load of the time window (21 checks): conversion of the window, and
  the real chunked send of `index.html` against a model of `rp_set_params()` (forceX handshake) plus a GET poll;
  the pages of v2.3.16 and of build 34 fail it (`--old`).
- `resources/config_tool.py`: the generated read mux uses the `_rd` copies and loads `sys_rdata` only on reads.

## v2.3.16 - Remote scope without the C controller, Time/Level trigger fields with units

### Added
- `control_finn.py`: `rp.scope_stop()`, `rp.scope_auto()`, `rp.scope_mode()` (also in `rp.osc`): stop / restart
  the scope of the C controller (web page) with `POST /data` `trig_mode` (2 = Single: its worker goes idle and
  does not arm the scope; 0 = Auto, 1 = Normal). Only `POST /data` is used (`GET /data` with another 2.0 App
  loaded crashes the nginx worker) and only when `/data` answers with this App.
- `test/trig_input_units_sim.js`: simulation of the Time / Level trigger fields (38 checks; `--old` shows the
  behaviour of v2.3.15).

### Changed
- `osc.measure()` / `rp.acquire()` stop the scope of the C controller first (`stop_web_scope`, default
  `rp.osc.auto_stop_web_scope = True`): after `bazaar?start` it acquires in Auto even with no page open and
  re-armed the scope with the `Dec` / `TrgDelay` written by Python, mixing its acquisitions with the ones of
  `/osc`. When it was running, `scope_stop()` waits until the controller has reset the scope (conf bits 0, 2,
  4 = 0 and `CurWpt` still); otherwise it costs one `POST /data`. `measure(wait=True)` warns if the page
  restarted its scope during the acquisition. `example_usage.py`: `scope_mode()` / `scope_auto()` cells.

### Fixed
- **"Time trigger" and "Level trigger" fields with units** (the units did not work since the first version
  of the page): they were `<input type="number">`, so "20 s" could not be typed (it stayed 20 ticks) and a
  pasted "19 s" was read as "" and sent as 0 (time trigger OFF). They are text fields now: Time accepts
  ticks or `s`, `ms`, `us` (`µs`), `ns`, `ticks` (e.g. `16.58 ms` = 2072500, `20 s` = 2500000000; up to
  2^32 - 1 = 34.36 s, larger values are clamped, a nonzero time below one tick is 1 tick); Level accepts counts or `V`, `mV` (-8192..8191, clamped).
  Decimal point or comma, space optional. The value is converted before it is compared with the last one
  (`lock_ctrl_update()` returned before converting when the number matched `trig_time`), the field is
  rewritten in ticks / counts only when the edit ends (it was rewritten while typing, so "20 ms" became 20
  at the "m"), and an empty or invalid text shows a hint and restores the last value instead of sending 0.
- Number fields of the page: an emptied field (e.g. with Backspace) is no longer sent as 0
  (`parseLocalFloat("")` = 0); the last value is restored.
- `control_finn.py`: **`POST /data` without answer in ~30 % of the requests** (found testing on the board).
  The `/data` handler of the Ecosystem (nginx module) only reads the body that arrives with the headers;
  `requests` / `http.client` send headers and body in two `send()` calls, so when they went out in separate
  TCP packets there was no answer (3 s timeout, warning "could not stop the scope…", CLOSE-WAIT connections
  left in the board) and, if it happened in the first `scope_stop()`, the acquisition went on mixed with the
  ones of the controller. `POST /data` is now sent in one `send()` (own socket, `Connection: close`, socket
  always closed), with `DATA_TIMEOUT` = 0.8 s per attempt and `DATA_RETRIES` = 2 extra attempts.
  `/lock`, `/osc`, `/calib` are GET requests (no body) and are not affected.
  Known issue of the Ecosystem (not fixed): every `POST /data` (also from `curl` or the web page) leaves one
  connection in CLOSE-WAIT in the nginx worker of the board (it answers `Connection: close` but never closes
  it; `GET /data` does not leak). The worker has 1024 file descriptors: after ~1000 POST the web server of the
  board stops answering until nginx is restarted. So `control_finn.py` keeps `POST /data` to the minimum:
  `scope_stop()` confirms Single once and remembers it; the next `measure()` / `acquire()` check with `GET /osc`
  reads only (`conf`, `TrgSrc`, `Dec`, `TrgDelay`, `CurWpt`, `TrgWpt` still across 50 ms and unchanged since
  the end of the last own acquisition) that the controller did not take the scope back, and POST again only
  when they changed (`scope_stop(force=True)` always asks). The check after `measure(wait=True)` uses the same
  reads; the `POST /data` `trig_mode` check is optional (`check_web_mode=True`). POST per call: `scope_mode()`
  1, `scope_auto()` 1, `scope_stop()` 0 while the cached Single holds, otherwise 1 (already Single) or 2;
  `acquire()` as `scope_stop()` (+1 with `check_web_mode`); `rp.osc.post_count` counts them. `GET /data` is not
  used (it crashes the nginx worker with another 2.0 App loaded). On the board: 20 `acquire()` after the first
  one made 0 POST; the page back in Auto between acquisitions was detected (2 POST, data not mixed).
- `control_finn.py`: when `scope_stop()` can not confirm Single (no answer after the retries, another App
  loaded, `trig_mode` not accepted, scope still running) `osc.measure()` / `rp.acquire()` raise the new
  `WebScopeNotStopped` (a `RuntimeError`) with the reason, without touching the scope, instead of a warning
  followed by a possibly mixed acquisition. `stop_web_scope=False` acquires anyway. `scope_stop()` returns
  False with a warning (reason in `rp.osc.scope_stop_error`). The docstring of `check_not_overwritten()`
  states that it does not detect a worker re-arming with the same `Dec` / `TrgDelay`.
- Page: after "40 s" (4294967295) the Time trigger field showed 4294967296, out of its range: the parameter
  is a float32 in the C controller (`params[].value`) and 0xFFFFFFFF comes back as 2^32 (float32 has no
  integer between 4294967040 and 2^32; the register is 0xFFFFFFFF, `lock_float_to_u32()` saturates). It can
  not be bounded in the float on the server side, so `loadParams()` clamps the received value to 4294967295.
  `test/lock_ctrl_ui_sim.js`: cases 6.1-6.2 (28 checks).

## v2.3.15 - HTTP remote control for Ecosystem 2.0, 32-bit lock time trigger

### Added
- `c/osc` / `c/osc.txt`: register **`TrgUnlock`** (offset `0x94`, index 37, write only, reads 0). The 2.0
  scope locks its trigger after every trigger (`TrgSrc` bit 5) until 1 is written there; `c/osc` could not
  do it, so an acquisition armed through `/osc` never triggered again.
- `control_finn.py`: `rp.acquire()`, `osc.unlock_trigger()`, `osc.acq_done()`, `osc.wait()`; PID
  (`set_pid()`, `get_pid()`, `pid_reset()`), ramp (`set_ramp()`, `get_ramp()`, `set_manual()`), lock-in
  (`set_signal()`, `set_gain()`, `set_freq_hz()`) and lock control (`lock_config()`, `lock_launch()`,
  `lock_now()`, `lock_release()`, `lock_status()`, `wait_locked()`, `get_lock_control()`) helpers.
- `test/lock_ctrl_tb.v`: cases 14-15 (time trigger and level+time with a time >= 2^31).

### Changed
- **Lock time trigger: 32 bits end to end.** `lock_ctrl.v` counter and comparator are 32 bits (they were
  31: `lock_trig_time` >= 2^31 aliased to `value - 2^31`, the counter wrapped at 17.2 s); the C controller
  converts the parameter as unsigned (`(int)` saturated at 2^31 - 1); the time field with units accepts up
  to 2^32 - 1 ticks (34.4 s, it was clamped to 4 s). New FPGA image.
- `pidA_sw` / `pidB_sw`: 4-bit registers (0..15), the width of the selector (16..31 aliased to 0..15).
- Register ranges of `c/lock.txt` / `c/osc.txt` (generated by `resources/config_tool.py`): `osc_ctrl` 0..3,
  `pidA_sw` / `pidB_sw` 0..15, `rl_state` 0..0 (fixed to 0, Re-lock disabled in `lock.v`), `Dec` 0..1048575
  (20-bit register; the App uses up to 524288).
- `Makefile`: `upload_html` (and `upload`, `upload_bit`, `upload_py`) depend only on `target/` (they needed
  `target_dbg` / `target_rld`, no longer made), use the `rw` script of the OS (2.0 or 0.9x) and check `RPIP`.

### Fixed
- `control_finn.py` on Ecosystem 2.0: `measure(wait=True)` / `wait_osc_finish()` waited forever (the end
  of the acquisition is now detected as in the C controller: `conf` bit 4, or `TrgSrc` = 0 and `conf`
  bit 2 = 0 on 0.9x); the trigger is unlocked before setting the source. Also: `np.float` (NumPy >= 1.24),
  `grid(b=...)` (Matplotlib >= 3.7), `set_lpf('all')` did not set F3, `get_lpf()` decoded the time
  constant with `& 31` (it is `& 15`), integer trigger channels, float values silently ignored by the
  server, calibration names missing in `calib -rv`, HTTP timeouts. `example_usage.py`: missing `import os`.
- `c/osc`: the register address is the `index` of the table, not its position.
- Descriptions of `X_28` / `Y_28`: X comes from `cos_ref` (in phase) and Y from `sin_ref` (quadrature);
  they were swapped (`config_tool.py`, `fpga_lock.h`, `main.c`, `lock.v` comments; no logic change).
- PID integrator divider (ISR, PID A and B options) value 4: label "65 us" (8 ns · 2^13 = 65.5 µs), it said "6 us".

## Documentation (after v2.3.14, not a new version)

### Added
- `doc/`: `App.md` (instruments and technical data), `Usage.md` (web interface and procedures, with
  screenshots in `doc/.Usage/`), `Structure.md` (layers and FPGA block diagrams), `FPGA.md` (register map
  checked against the RTL), `Remote.md` (HTTP remote control), `Devel.md` (build and tests).
  `doc/README.md` is now the index of `doc/` (its register table moved to `FPGA.md`). README updated.

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
