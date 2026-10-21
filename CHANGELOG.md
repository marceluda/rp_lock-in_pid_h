
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

## v2.3.28 - 2026-10-20 - Quick trigger buttons time / level / time+level in Lock Control (web page only, no FPGA / C change)

Requested by the user (2026-10-20): one click on a button and one on the graph instead of Trigger type + Choose from
graph + click + Trigger Lock.

### Added (web page)
- **Lock Control**: three small buttons stacked between **Trigger Lock** and **Lock Now**: **time** (orange),
  **level** (blue), **time+level** (purple); dark border, light fill. A click on one of them sets the lock trigger
  type for Trigger Lock (Time trigger / Level Trigger / Level+time Trigger) and waits for a click on the graph, as
  *Choose from graph* (the *config* section is not opened). The button stays filled with its color while it waits,
  the cursor over the scope is a crosshair, and a short message below the buttons says what the click will set (with
  the red warning of *Choose from graph* when t = 0 of the plot is not the scan floor). The message is drawn over the
  rows below (state label, checkboxes) with a border of the button color: the panel does not grow nor move while it
  waits (testAgent 2026-10-20: the 2-line text pushed the checkboxes down), and clicks go through it.
- Layout (user review of 2.3.27-68): *Trigger Lock*, the column of the three small buttons and *Lock Now* are one flex
  row; the column is as tall as the big buttons and spreads the three in it, so the block is centered in height with
  them. The small buttons are a bit smaller (16 px, 18 before) and *Trigger Lock* / *Lock Now* a bit larger (16 px
  font, 60 px high instead of 48 px). In a narrow left column (container query, row narrower than 235 px, e.g. a
  1366 px wide window) all of them are a bit smaller so that they stay in one row; in a very narrow one (below ~190 px)
  *Lock Now* goes to a second line.
- The click on the graph sets the trigger type and the time (from the scan floor) and / or the level, and fires
  **Trigger Lock** at once, always (as *Fire on click*, whatever its checkbox says), with **Capture Lock** if it is
  checked: one lock request (2 POSTs, as Fire on click).
- While waiting nothing is sent: an ARMED / LOCKED lock stays as it is until the click; then it is released and armed
  again with the new values (as Fire on click). A 2nd click on the same button, Esc or *Choose from graph* cancel;
  another of the three buttons changes the type. On a frozen capture locked by level (lock time unknown) *time* keeps
  waiting (warning) and *time+level* sets only the level, as *Choose from graph*.

### Fixed (web page)
- A click with *Choose from graph* + *Fire on click* while another POST was in flight (busy server, a change made just
  before) lost the new time / level: `loadParams()` (`trigger_just_set`) wrote them into the server values, so they
  looked sent and never were, and Trigger Lock fired with the old ones. Now only values already sent are protected;
  pending ones are kept by `unsentChanges()` and sent after that POST (also the trigger type of the quick buttons).
- With the lock **LOCKED** and a POST in flight at the click on the graph (quick buttons, or *Choose from graph* +
  *Fire on click*), the new time reached the register but neither the release (`lock_ctrl_aux_launch_lock_trig` = 0)
  nor the new request (1) was sent: the lock stayed at the old point, the counter did not change and "LOCKED but not
  captured" appeared (testAgent on RP2, POST delayed 1.7 s). The send queued during a POST runs 100 ms after its
  answer; in that gap `lockWhenIdle()` saw nothing busy, wrote the request 1 (the value the server already had) and
  sent it, so the key was not in the POST and the 0 was never sent. Now that delayed send is kept in
  `send_que_timer` and `lockWhenIdle()` waits for it: the release goes first, then the request.

### Tests
- New `test/lock_quick_trig_sim.js` (harness of `lock_capture_ui_sim.js`, handlers of the page): layout and
  colors, each button sets its type and waits without POST, one click on the graph → values + one lock request,
  LOCKED and captured (with Fire on click unchecked and trigger type OFF before), cancel (Esc / same button /
  Choose from graph), another button, pressed while ARMED / LOCKED, Capture Lock off, frozen capture by level, POST in
  flight (also *Choose from graph*), LOCKED + POST in flight of 150 ms / 1.7 s and at 60 moments around its answer
  (buttons and Fire on click, with and without Capture Lock), the message does not move the layout, the row of the buttons (flex, centered). 57 checks;
  with the v2.3.27 page: 51 fail. The other simulations pass.

## v2.3.27 - "Load last config on init", Load last config / Reset to defaults; Lock Control below Outputs (web page only, no FPGA / C change)

Requested by the user (2026-10-20): the App opened with the parameters of a previous session; the user wants to choose.

### Changed (web page)
- **Lock Control** panel moved right below **Outputs** in the left column (Oscilloscope, Outputs, Lock Control,
  Lock-in modules, Ramp Controller, PIDs modules, Streaming). Only the position of its HTML changes.
- The state that the page saves automatically (`saveState()`: the Config parameters, time window, exact streaming IP
  and Capture Lock / Fire on click preferences, every ~2 s and after each POST) is now also kept in **localStorage**
  (`lockin_last_state_<app_id>`, shared by the tabs, survives closing the browser): the **last config**. The tab state
  (`sessionStorage`, used by *Restart*) is kept as before.
- Config dialog, new checkbox **Load last config on init** (`#load_last_on_init`), **checked by default**, saved in
  localStorage (`lockin_load_last_on_init_<app_id>`). When the page starts the App (opened from the main menu, a new
  tab, F5): checked, the last config is restored (up to 2.3.26 the state of the tab was restored, so a new tab always
  started with defaults); unchecked, only `def_params` are sent: the App runs with the defaults of `src/main.c`
  (`rp_main_params`) loaded by its start. The ramp / PIDs of a restored config follow *Don't turn on PIDs and Ramp on
  config loading* (unchecked by default); lock requests are never restored.
- Config dialog, new buttons **Load last config** and **Reset to defaults**: they close the dialog and restart the App
  (page reload; the App is stopped and started as when it is opened, the FPGA is reloaded) restoring the last config /
  with the defaults, whatever the checkbox says. *Reset to defaults* therefore gives exactly the parameters of a fresh
  App (no table of defaults in the page that could drift from `main.c`), with the lock open and no lock request.
- Opened with the defaults (unchecked, or *Reset to defaults*) the last config is **kept** (hold,
  `lockin_last_hold_<app_id>`) until the user changes a parameter (time window / Y axis alone do not count): *Load
  last config* then still brings it back.
- *Restart* (after "took control" and in the error dialogs) and the automatic restarts after the worker died still
  restore the **tab state**, with the checkbox checked or not. An App already running when the page opens (another
  tab, or a reload whose stop on unload was not sent) keeps its state as before; for *Load last config* / *Reset to
  defaults* it is stopped and started.

### Tests
- New `test/last_config_sim.js` (35 checks: HTML and panel order, checkbox default and persistence, restore on init
  checked / unchecked, hold, the two buttons, Restart and recoveries). It fails with the page of 2.3.26. The other node
  tests unchanged and passing.

## v2.3.26 - Auto waits for the trigger (forced only after a time limit); "Don't turn on PIDs and Ramp on config loading" unchecked by default (no FPGA change)

Requested by the user (2026-10-19): loading a config switched the scan off; it should start scanning if it was
scanning when the config was saved. This change is in the web page only.

### Changed (web page)
- The option **Don't turn on PIDs and Ramp on config loading** (Config dialog, `#load_config_block_start`) is kept
  but is now **unchecked by default** (it was checked). Unchecked, *Config → load* (and *Load file*, which goes through
  the same load) and the restore of the tab state after a start / *Restart* (`restoreState()`) set
  `lock_ctrl_aux_ramp_enable_ctrl`, `lock_ctrl_aux_pidA_enable_ctrl`, `lock_ctrl_aux_pidB_enable_ctrl` and
  `lock_ramp_enable` (*Scan enable*) as saved. Checked, they are set to 0 as before. The lock requests
  (`lock_ctrl_aux_lock_now`, `lock_ctrl_aux_launch_lock_trig`) and the other transient commands
  (`state_transient_zero`) are never loaded, with or without the option.
- The option is not saved (configs, tab state, localStorage): every page load starts unchecked. The checkbox has
  `autocomplete="off"` (a browser that restores form fields on reload, e.g. Firefox on F5, could otherwise show a
  state different from the variable)
  and the variable is synced from the checkbox when the handlers are set.

### Tests
- New `test/config_load_block_sim.js` (10 checks: default unchecked, Config load and Restart restore ramp / Scan enable
  / PIDs as saved, checked keeps them off, lock requests always 0). With the page of 2.3.25 6 of them fail.
  The other node tests unchanged (they set the option explicitly).

### Changed (controller, `src/worker.c`; web page): Auto waits for the trigger
Reported by testAgent (2026-10-19, lock_in+pid_square 2.0.3/2.0.4 on RP2; `reportes/lock-in_pid_sq.md`): with Ext Trig =
Scan floor the trace sometimes started at the ceiling of the scan. Cause: in **Auto** the scope triggered at once
(`osc_fpga_cnv_trig_source(trig_imm = 1)` = manual trigger source in `src/fpga.c`), so t = 0 fell on any phase of the
scan; the Ext Trig (and the level of a channel) only worked in Normal / Single. The config of the user had Auto.
- Auto now arms the real trigger source (as Normal) and the worker forces the acquisition (manual trigger source)
  only if no trigger came within a time limit counted from the moment the trigger is enabled
  (`rp_osc_auto_timeout_us()`): max(0.25 s, 1.1 x window + 50 ms, 1.1 x period of the Ext Trig + 50 ms), at most 80 s.
  The period is known for Scan floor / Scan ceil when the scan runs (Scan enable on, not in reset, effective ramp
  enable of `lock_ctrl.v` = `lock_status` bit 4; same formula as `rampPeriodCycles()` of the page) and for harmonic mod. (2520 x (hp+1) cycles).
  Choice of the values: 0.25 s keeps the free view (no trigger) at ~4 traces per second and is longer than the default
  64 ms scan; 1.1 x window lets a signal whose period fits in the window always trigger in time; 1.1 x period makes a
  slow scan behave as Normal (30 s scan, window 0..29.4 s: limit 33.05 s; the next floor comes ~0.6 s after the
  re-arm, so every scan is acquired from its floor); a stopped scan (or LOCKED with the ramp off) gives no period term,
  so Auto does not wait a whole period for a floor that will not come. 80 s > the longest window (68.7 s).
- Unchanged: Normal and Single (never forced), the Auto window (from the trigger, t = 0 .. xmax, no pre-trigger, as
  `src/main.c` sets it for Auto), the resume of an acquisition across POSTs that do not change it (the limit is
  recomputed and keeps counting from the same moment), the long acquisitions of 2.3.23 (forced or not, the reader
  starts at the trigger), Capture Lock (Single + Ext Trig 128) and AUTO (its own immediate acquisitions).
  `scope_acq_state` is 2 (armed) while Auto waits and 3 after the (real or forced) trigger.
- Page: the trigger *Level* field, its line and slider are enabled in Auto too (they were only for Normal); the
  "Choose from graph" warning no longer asks for Normal/Single (Auto + External + Scan floor gives t = 0 at the floor).

### Tests (Auto)
- `test/auto_set_c_sim/harness.c` section 10 (`SIM_AUTO=1 test/auto_set_c_sim/run.sh` runs only it): 10.1 Auto + Scan floor
  every 3 s, window 0..2.94 s: every trace from a floor, none forced; 10.2 scan stopped, window 0..0.1 s: forced every
  ~0.40 s (0.25 s + the acquisition); 10.3 3 s scan seen in 0..0.1 s: only floors (period term); 10.4 Normal without
  trigger: nothing. With the `src/` of 2.3.25: 10.1-10.3 fail (immediate triggers). 6.1 runs 9 s (Auto without trigger
  waits 2.25 s now) and section 8 waits 0.6 s for an Auto trace in ms.

## v2.3.25 - Single (select) completes a long acquisition; no "Square mod." in the Ext Trig menu (no FPGA change)

Reported by testAgent (2026-10-16, v2.3.24 on RP2): with a 30 s scan in Normal, choosing *Mode = Single* in the
select in the middle of the scan left the trace cut (at 27.42 s) and it never grew.

### Fixed (controller, `src/worker.c`)
- Choosing *Single* in the Mode select sends only `trig_mode` 2: `rp_set_params()` puts the worker in idle, and the
  worker abandoned the long acquisition in progress (`trig_mode` is an acquisition key and the change also asked for
  an FPGA update / scope reset), so no more data were published and the page kept the last partial trace. Now, when
  the worker goes to idle with a long acquisition already triggered and the parameters differ only in `trig_mode`,
  that acquisition is finished (the reads go on, the FPGA update is deferred to its end) and published as the
  Single trace. The *Single* button, another mode or any other change abandons it as before. `scope_acq_state` is
  set to 0 when an acquisition is abandoned (it stayed at 3, "acquiring").

### Changed (web page, `resources/config_tool.py`, `control_finn.py`)
- The "Square mod." Ext Trig (16) is no longer in the trigger menu: it is not implemented in this App (always 0 in
  the FPGA). Also removed from `resources/config_tool.py`; labelled "0 (Square mod.)" in
  `resources/remote_control/http_version/control_finn.py` (as in lock_in+pid_harmonic_hf / _harmonic2).
- The `<title>` and page title of the source `index.html` said v2.3.22 (the Makefile writes the version in the
  target); now v2.3.25.

### Tests
- `test/auto_set_c_sim/harness.c`: scenario `SIM_SINGLE=1 test/auto_set_c_sim/run.sh` (window 0..2.94 s, scan floor
  every 3 s, Mode select -> Single at x = 2 s): checks S.1 trace completed up to xmax, S.2 `scope_acq_state` not left
  at 3, S.3 Single button afterwards (2.3.24: S.1 and S.2 fail, trace frozen at 2.0 s).
- `test/osc_presets_sim.js`: 4.7, the Ext Trig menu has no "Square mod.".

## v2.3.24 - Scope presets (OscA|OscB) and Ext Trig sets the Trigger panel (web page only, no FPGA / C change)

### Added (web page)
- **Presets of the scope signals**: six small buttons in the *Oscilloscope* panel, below *Ext Trig* (row
  *Presets*, two rows of three; 42x20 px, label in one line, 10 px bold). Blue: `in1|in2` (OscA = in1, OscB = in2), `in1|ctrl` (in1, ctrl_A), `X|Y` (Xo, Yo);
  green: `in1|err` (in1, error), `ctrl|err` (ctrl_A, error) and `usr`. A click sets OscA/OscB (mux values 1, 2, 3, 4,
  17, 18 of the selects) through the same path as the two selects: one POST with only `lock_oscA_sw` /
  `lock_oscB_sw` (and the usual `single_btn`/`xmin`/`xmax` with their current values); the zoom (time window and
  Y axes), the trigger (Mode, Source, Edge, Level, Ext Trig) and a Capture Lock are not touched. The title of each
  button shows its two signals.
- **`usr` preset**: a pair chosen by the user. Double click (or a click while it is not configured, dashed border)
  opens a dialog with two selects (the options of OscA/OscB; the first time, with no pair saved, it offers
  OscA = pidA_out (*PID A out*, 10) and OscB = error (3); afterwards the saved pair); *Accept* saves the pair in the browser
  (`localStorage`, key `oscUsrPreset_lock_in+pid_harmonic`) and shows it; the title of the button gives its two
  signals. The pair is part of the page only (the controller has no such parameter): it is saved in the configs
  (*Config* save and download json, in `ui.ui_osc_usr_a` / `ui.ui_osc_usr_b`, never sent to the server) and a
  *Config load* of a config that has it takes it (and stores it); configs without it keep the current one. The
  first click of a double click applies the pair already saved (at most one POST); the dialog opens once.

### Changed (web page)
- **Ext Trig sets the Trigger panel**: when the user picks in *Ext Trig* a value different from the current one
  and not *None*, the *Trigger* panel goes at once to *Source* = External and *Mode* = Normal, in the same POST as
  the Ext Trig (from *Single* the page polls again, as with a change of Mode). *None* changes nothing else. Only the
  user change of the select does it: *Config load*, the restore at the end of a Capture Lock, *Reset zoom* and
  *AUTO* set their own values (they do not go through the handler of the select). Changing Ext Trig during a Capture
  Lock ends it (as before) and then applies the rule; the restore and the new values go in one POST (before, a GET
  started by the restore could send them in two).

### Tests
- New `test/osc_presets_sim.js` (37 checks; the page of 2.3.23 fails 32). `test/config_load_window_sim.js`: stub of
  `oscUsrConfigLoad()` (the function is mocked there).

## v2.3.23 - Slow scans: scope trace, Capture Lock, Reset zoom and time trigger after a stopped ramp

Reported by the LOCK MODE test with a 30 s ramp (2026-10-15, v2.3.22 on RP2): the lock worked (19/19), but the scope
trace mixed old data, Capture Lock caught 2 of 7 locks and warned "LOCKED but not captured" while still acquiring.

### Fixed (controller, `src/worker.c`, `src/main.c`, `src/lock.c`)
- **Trace mixed with an older lap of the scope memory** (windows >= 1.5 s, read while the FPGA writes them). The reader
  inherited from the RP 0.9x scope (`rp_osc_decimate_partial()`) followed the buffer with its own index: when it
  wrapped (16383 -> 0) before the write pointer, or when the window started after the trigger (xmin > 0), it read
  samples written 68.7 s before (one lap at Dec 524288) as new ones, and returned `OK` with them. New reader: every
  point is a sample counted from the trigger; it is read only if it was written in this acquisition (count of the
  samples written since the trigger, from the write pointer), not overwritten yet, and not older than the history of
  the acquisition (pre-trigger samples: FPGA counter `adc_we_cnt`, register 0x2C, or the time the trigger was kept
  disabled). Other points are never shown (the trace starts / ends at the valid ones; partial traces no longer
  show the previous trace to the right). `OK` only when the acquisition is complete. The trigger is detected with
  the trigger status bit (a reset also changed the trigger pointer).
- **Capture Lock lost with slow scans**: the POST "Single + lock request" waited at most 1.5 s for the scope, but
  with a long window the scope needs |xmin| (7-9 s) of history before its trigger is enabled: the lock came first
  and its pulse "Lock control trig" was missed; the POST took ~2 s, the page sent it again and the scope was armed
  again (another |xmin| of wait). Now the POST answers at once and the request bits are held out of `lock_control`
  until the worker has enabled the trigger of that acquisition (deadline: history + 3 s). A release, or a value
  written from outside, drops the held request.
- The pre-trigger wait of the worker is no longer blind: a new POST is looked at during it, and new parameters that
  do not change the acquisition (e.g. the same Single POST sent again) resume it instead of arming again. Single
  with `single_btn` goes straight to the Single state (no idle in between).
- **One scan of every two with Reset zoom on a slow scan**: the acquisition ended after the next scan floor (the
  controller makes the window a bit longer: 1024 points, e.g. 0..30.06 s). Long acquisitions now end at the end of
  the window of the user (points after it are not waited for) and the last points are read as soon as they are
  written, so the scope is armed again in time.
- A change of the time units (e.g. Reset zoom from ms to s) replaces the trace in the old units at once (it was
  drawn ~10 s on the new axis).

### Added (controller)
- Read-only parameters `scope_gen` (generation of the scope parameters), `scope_acq_state` (0 none, 1 loading the
  history, 2 waiting for the trigger, 3 triggered / being read, 4 complete), `scope_acq_gen` and `sig_gen`
  (generation of the trace served). `PARAMS_NUM` 208 -> 212 (appended after the lock parameters).

### Fixed / changed (web page)
- Capture Lock: a trace is the capture only if it comes from the capture acquisition (`sig_gen`); its partial traces
  are drawn while the window after the lock is acquired. "LOCKED but not captured" only when the scope of the
  capture still waits for its trigger 2 s after LOCKED (it appeared after 2 s of LOCKED while a 30 s capture was
  being acquired). New banners: "loading the scope history before the lock (x s)", "lock captured, acquiring the
  trace...".
- Reset zoom on Scan floor / Scan ceil / harmonic mod. with a period >= 1.5 s: window 0 .. 0.98 x period (at least
  50 ms before the next trigger) so that every scan is acquired. Shorter periods: one whole period, as before.
- Reset zoom clears the plotted trace and ignores the data of GET /data started before its POST is answered.

### Fixed after the retest of build 51 on RP2 (2026-10-15 19:17)
- **Time trigger in the middle of a scan, far from the peak (FPGA, `lock_ctrl.v`).** The counter of the time
  trigger was reset only at a scan floor, kept counting while the ramp was stopped (LOCKED with "set ramp" off, the
  ramp disabled or in reset) and wrapped every 2^32 x 8 ns = 34.4 s. After a release the ramp goes on from where it
  stopped while the counter still counted from the old floor, so a time trigger armed then fired before any floor
  (RP2: 4.4 s after the request, ramp at -0.28 V). Now the counter is valid (`cnt_ok`) only from a floor of a ramp
  that has been running since then: it is cleared while the effective ramp enable of the lock control (lock_status
  bit 4) or the ramp generator (`ramp_enable` and not `ramp_reset`, new input `ramp_run`) is off, and set at the
  next floor. The time trigger and the level-after-time trigger need it, and the counter saturates instead of
  wrapping. A request armed after a stop (from the page, Python or `py/lock_from_registers.py`) waits for the next
  floor and fires at floor + time; with the ramp running nothing changes (same clock cycle as before).
- **Capture Lock request applied only at its deadline** (RP2: 10.9 s, "scope not armed in time") when it came while
  the capture of the same window was still waiting: the worker resumed that acquisition without saying it was
  armed. It does now, and the POST also checks the arm the worker already published (the worker may resume before
  the request is held). An acquisition already triggered is not resumed by a new Single any more (a new capture
  request would have taken the trace of an older event).
- (A software workaround of build 55, a ramp monitor in the controller that held time requests until a floor, was
  replaced by the FPGA fix: it did not cover requests written directly to the FPGA nor ramps longer than 34.4 s.)

### Notes
- Lock Now with Capture Lock on a slow window locks after the history before it is loaded (30 % of the window,
  e.g. 9 s for 30 s), on purpose: the capture shows that history.
- Windows < 1.5 s at Dec 65536 (e.g. a 1 s scan) are not read while written: the scope ends each acquisition after
  a whole memory (8.6 s), as before.
- `example_usage.py`: `time=16.58e-3` / `timeout=10` are for the 64 ms scan of the lock tests (see the note there).

### Tests
- `test/auto_set_c_sim` (real C, native): model of the circular buffer of the scope FPGA (write pointer that wraps,
  trigger pointer, `adc_we_cnt`, post-trigger delay, conf bits; every sample holds its number) and of the lock pulse:
  long windows in Auto with xmin > 0, Normal + Scan floor every 3 s with a 0.98 T window (every scan), a read that
  catches the write pointer at the end of the buffer, Capture Lock with 1.8 s of history (Lock Now, Trigger Lock,
  POST sent again, release, kp while held), the 64 ms case, change of units. With the C of 2.3.22 9 fail (all but
  the 64 ms case, which works in both). Section 9, model of the ramp and of `lock_ctrl.v`: 9.0 the model of the
  old FPGA reproduces RP2 (Trigger Lock, time 1 s, right after releasing a lock closed 0.3 s after a floor: lock at
  phase 0.70 s without a floor); 9.1 from the page and 9.3 written directly to `lock_control` with the new FPGA:
  floor + 1.000 s after a real floor; 9.2 a new capture request while the capture of the same window waits (4 times):
  applied in <= 2 ms (build 51: 4.8 s, at its deadline). 44/44; with the C of build 51 only 9.2 fails (9.1 and 9.3
  are done by the FPGA now).
- `test/lock_ctrl_tb.v` (xsim): the test ramp stops with the effective enable / `ramp_run`, as `gen_ramp`; cases
  16-19: normal case unchanged (floor + 300 of the same scan), release mid-scan + time trigger (next floor + 300),
  ramp generator stopped (no lock until it runs and passes a floor), counter saturation. 45/45; the old
  `lock_ctrl.v` fails 7.
- `test/lock_capture_ui_sim.js`: section 8, 30 s scan (Time, Level, Lock Now, arming POST answered after 2.5 s,
  missed lock warning, model of the C of 2.3.22): 79/79; with the page of 2.3.22, 8 fail.
- `test/reset_zoom_sim.js`: 0.98 T cases and trace clearing, 29/29.

## v2.3.22 - Mouse wheel on the scope: both axes, SHIFT = time only, ALT = Y only (no FPGA change)

### Added (web page)
- Mouse wheel over the oscilloscope plot, zoom centred on the mouse, 1.5x per step:
  - **no key**: both axes (time and the two Y axes), as before;
  - **SHIFT** held: the time axis only; while SHIFT is down with the mouse over the plot the cursor is a horizontal
    double arrow (`ew-resize`). SHIFT + wheel arrives as a horizontal scroll (`deltaX`) in Chrome and in some
    Firefox versions: both directions are handled;
  - **ALT** held: the Y axes only (both of them; counts in raw mode), cursor vertical double arrow (`ns-resize`).
    The ALT key alone over the plot is not passed to the browser (Firefox showed its menu bar on release; ALT + wheel
    was history back/forward there); ALT + another key (shortcuts) is not touched.
  - The cursor follows the keys without moving the mouse (keydown/keyup) and goes back to normal when the mouse
    leaves the plot, the key is released, the window loses the focus or the tab is hidden.

### Changed (web page)
- The wheel over the plot is no longer handled by `jquery.flot.navigate` (`zoom.interactive: false`), which zoomed
  both axes with any key and without limits, but by the page (`[PLOT WHEEL]` block of `index.html`).
- The time window still goes to the controller through the same debounced path (one POST 250 ms after the last
  step; the controller chooses the decimation and the page follows its time units), and now stays between 20 ns
  and 68.7 s (one memory at the largest decimation, the limits of the X-/X+ buttons). A Y-only zoom sends nothing.
  Y range limited to 1/2048 ... 1000 x full scale (2 V, or 16384 counts in raw mode).
- During a lock capture (Capture Lock, waiting or captured) the wheel zoom is only in the page: before, its time
  window was sent to the controller and could change the decimation and units of the frozen capture. Ending the
  capture (AUTO, Reset zoom, ...) restores the window saved before it, as before.
- The wheel over the number fields (SHIFT x10, CTRL x100) does not change.

### Fixed (web page)
- A zoom (wheel, pan, touch or mouse selection) sent the time window rounded to 2 decimals of the current time
  units (`toFixed(2)`): a window under 0.01 units, e.g. a quick zoom-in from s to -0.50 .. 0.98 ms, was sent as
  xmin = xmax = 0 and the controller answered 0 .. 1 us. Now it is sent with 12 significant digits, and never with
  xmax <= xmin. (The X-/X+ and offset buttons already sent it unrounded.)

### Added
- `test/plot_wheel_sim.js`: the `[PLOT WHEEL]` block and the `plotzoom` debounce of `index.html` with a mocked
  plot / jQuery / `jquery.mousewheel` (wheel with and without SHIFT/ALT, deltaX/deltaY, cursor on keydown/keyup,
  mouseenter/leave, blur and hidden tab, limits in the three time units and in raw mode, debounce, Capture Lock,
  window sent without rounding), 59 checks. With the page of v2.3.21 (the `navigate` handler) 31 of them fail; the
  no-key zoom passes with both.

### Note
- Some window managers on Linux take ALT + wheel (or ALT + drag) for themselves; then the browser never gets the
  wheel event with ALT and the Y-only zoom can not work there.

## v2.3.21 - "Reset zoom" fits the scope to the period of the trigger source (no FPGA change)

"Reset zoom" used to set the time window to 0..130 us (Dec 1, the server "reset zoom" request) whatever the trigger,
and Y to +-gui_reset_y_range/2 also in raw mode (+-1 count there). Now it depends on the Oscilloscope *Ext Trig*:

### Changed (web page)
- Ext Trig = **Scan floor** or **Scan ceil**: X = one period of the Ramp Controller as `gen_ramp.v` generates it,
  sawtooth `(high-low+1)*(step+1)`, triangle `2*(high-low)*(step+1)` clock cycles of 8 ns (the same function as
  Choose from graph, `rampPeriodCycles()`; measured on the RTL by `test/ramp_mod_period_sim.sh`).
- Ext Trig = **harmonic mod.**: X = one period of the local oscillator of the lock-in, `2520*(hp+1)` cycles
  (`gen_mod_h.v`, f = 125 MHz / (2520 (hp+1))).
- Other Ext Trig (or a ramp with high <= low): X = one whole memory of the scope at the current Dec,
  16384 * 8 ns * Dec.
- The window starts at t = 0 (the trigger). It is applied as a zoom: the server picks the Dec from it (the smallest
  one whose memory covers the period, so a period longer than the memory takes a larger Dec and a shorter one a finer
  Dec) and the page follows the automatic time units (forceX). The window is kept 1 ppm under a whole memory, since
  the server keeps xmin/xmax in float and one memory exactly would round up to the next Dec (x8). Periods longer than
  the longest memory (68.72 s, Dec 524288) are clamped to it.
- Y: -1 V .. +1 V; in raw mode -8192 .. 8192.
- During a lock capture (Capture Lock), Reset zoom first ends it as AUTO does: the scope settings saved before the
  capture are restored (trigger mode, source and Ext Trig; console "Capture Lock: ended by Reset zoom") and the
  window follows the restored Ext Trig (e.g. Scan floor -> one ramp period).
- The Raw Mode button rescales Y as Reset zoom does (-8192 .. 8192 / -1 .. 1 V); X does not change.
- Tooltip of the button with this behaviour; `doc/Usage.md` updated. No change in C (version only), FPGA or registers.

### Added
- `test/reset_zoom_sim.js`: the real `resetZoom()` against a model of the time range code of `src/main.c` (float32
  xmin/xmax, Dec, units, forceX): the three cases, Dec limits, raw mode, Reset zoom during a capture and the Raw
  Mode button, 26 checks. With the page of v2.3.20 (`--old`) 25 of them fail.
- `test/ramp_mod_period_tb.v` / `test/ramp_mod_period_sim.sh` (Vivado 2020.1 xsim): periods of the ramp floor/ceil
  triggers (triangle, sawtooth up/down) and of `harmonic_trig` on the RTL, 10 checks.

### Note
- The period shown under *Ramp period* in the Ramp panel is `(high-low)*(step+1)*8 ns*(2-sawtooth)`: right for the
  triangle, but one step (`(step+1)*8 ns`) short for the sawtooth. Not changed (the conversion of that field is still
  to be reviewed).

## v2.3.20 - FPGA: lock-in references delayed 1 clock (phase of v2.3.18 through the DAC)

In v2.3.19 the outputs to the DACs got a register, so the modulation that goes out through `out1`/`out2` and comes
back to `in1` was 1 clock (8 ns) later with respect to the reference of the lock-in: the measured phase changed by
-360 deg * f * 8 ns (-0.143 deg at 49.6 kHz, measured -0.185 +- 0.045 deg on RP2). v2.3.20 delays the references
into the multipliers of the lock-in 1 more clock, as in `lock_in+pid` 2.2.8, `lock_in+pid_harmonic_hf` 2.3.13,
`lock_in+pid_harmonic2` 2.4.6 and `lock_in+pid_square` 2.0.1: in a loop through the DAC the lock-in sees the phase
of v2.3.18 again, at every frequency and harmonic.

### Changed (FPGA)
- `lock.v`: `sin_ref_d`, `cos_ref_d`, `cos_1f_d..cos_3f_d` (+1 clock) into the five multipliers of the lock-in.
  The references that go to the modulation, the scope and the slow DACs are not delayed. Latencies from `in1` do
  not change (`in1` -> `Xo` 3 clocks, LOCK MODE loop +32 ns as in v2.3.19).
- Timing (Vivado 2020.1): WNS -0.888 ns (v2.3.19: -1.099), TNS -217.4 ns (-207.5), 762 failing endpoints (774),
  adc_clk -> dac_clk_1x +0.680 ns. `red_pitaya.bit` / `fpga.bit.bin` rebuilt. No change in C, page (version only)
  or registers.

### Added
- `test/lock_latency_tb.sv`: the lock-in scenarios use `in1` delayed 2 clocks (the modulation leaves 2 clocks later)
  and a new scenario S7 closes the loop `out1` -> "system" (3 clocks, gain 3/4, offset) -> `in1` for each model:
  `Xo..F3o` = those of v2.3.18 delayed 4, bit exact (442 checks). With the `lock.v` of v2.3.19 it fails (S7: `Xo`,
  `Yo`, `X_28` differ), i.e. it checks the compensation. `doc/lock_latency.md` updated.

## v2.3.19 - FPGA timing: pipeline registers in the lock-in, PIDs, generator and outputs

The FPGA did not meet timing at 125 MHz (WNS -8.954 ns, TNS -9565 ns, 5101 failing endpoints): long
combinational chains of the loop (generator ROM -> product -> LPF / bypass -> gain -> saturation -> PID / scope /
lock control; PID sum -> ctrl -> out mux -> modulation -> DAC). With the approval of the user to add latency,
v2.3.19 registers those chains: **WNS -1.099 ns, TNS -207.5 ns, 774 endpoints** (adc_clk -> dac_clk_1x
-8.789 -> +1.123 ns; what is left: recursive loops of the LPF and the PID integrator, in1 -> PID input, and paths of
the oscilloscope outside the lock module). Same behaviour except for the latencies, checked bit by bit in simulation
against v2.3.18. Details, latency of each signal and timing per group: `lock_in+pid_harmonic/doc/lock_latency.md`.

### Changed (FPGA)
- Added latency (8 ns per clock): generator outputs (`sin_ref`, `cos_ref`, `cos_1f..3f`, `harmonic_trig`) +1;
  lock-in outputs `Xo`, `Yo`, `F1o..F3o` +2 (register at the output of the first LPF stage and after the gain /
  saturation); bus reads `X_28..F3_28` +1; PID outputs +1 (`lock_pid_block` output registered, enable delayed with
  it); `out1`/`out2` +1 for everything that goes to the DACs. LOCK MODE loop (in1 -> Y -> PID A -> out1): +32 ns.
  The modulation that goes out through `out1` is 1 clock later than the reference: in a loop through the DAC the
  phase of the lock-in changes by -0.143 deg at 49.6 kHz (one step of `gen_mod_phase` at hp 0), less at lower
  frequencies; not compensated.
- Same values with fewer logic levels: `lock/shift_sat14.v` (gain + the two saturations of `Xo..F3o` in one test),
  `sum_div` of the second LPF stage kept in a register (a change of `lpf_F*` reaches it 1 clock later), `sat14`
  without barrel shifter, integrator of the PID with the ISR shift in parallel with the saturation.
- `red_pitaya.bit` / `fpga.bit.bin` rebuilt (Vivado 2020.1). No change in C, page (version only) or registers.

### Changed
- `resources/remote_control/http_version/example_usage.py` (Lock cell, `lock_mode`) and the PID example of
  `doc/Remote.md`: PID A kp -250 (was -500), as the `*__lock_mode*.json` test configs since 2026-10-12 (approved by
  the user: with -500 the loop was at the edge of oscillating, ~4.7 kHz).

- Page title (`h2.page-title`) said v2.3.18; the build now writes the version of `info/info.json` in it and in
  `<title>` (Makefile, target/), so they cannot fall behind again.
- `c/streaming.c`: `perror("[+] Finishing streaming")` -> `fprintf(stderr, ...)` (with errno 0 the log said
  ": Success"), as in `lock_in+pid_harmonic_hf` 2.3.12 / h2 2.4.5.

### Added
- `test/lock_latency_sim.sh` + `test/lock_latency_tb.sv` (xsim): `lock.v` of the working tree side by side with the
  one of v2.3.18 (or another commit), 412 checks of the latency of each signal, bit exact (lock-in with the LPFs on,
  bypassed and with every gain, PIDs with every PSR/ISR/DSR/SAT, modulation, Level trigger, step responses).

## v2.3.18 - Minor fixes found in the tests (no FPGA change)

The FPGA image is the one of v2.3.17 (only comments of `lock.v` changed).

### Fixed
- **Lock trigger registers written from Python** (`py/lock_from_registers.py --time/--level/--sw`, `control_finn.py`):
  the page never showed them and the C controller wrote its own copy back at the next change of any lock parameter
  in the page (a lock armed from Python with `--time 100ms` then fired at the 18 ms of the page). `lock_trig_val`,
  `lock_trig_time` and `lock_trig_sw` now follow the rule of `lock_control` (v2.3.13): `lock_update()` writes each one
  only when its parameter changes, and `lock_update_status()` (every request) copies a value written from outside to
  the parameter, so the page shows it and keeps it. Above 2^24 ticks the parameter is the float32 rounding, the
  register keeps the exact value. `lock_init()` resets this memory (and the one of `lock_control`).
- Config -> load: the send of the whole config no longer includes read-only parameters of the server (`meas_*`,
  `lock_X/Y/F1..F3`, `lock_lock_status`, `lock_lock_control`, `trig_delay`, ...; `server_ro_keys`, the read-only
  list of `src/main.c`). The server ignored them; they only made the POSTs bigger (8 POSTs, 203-231 keys).
- **Single mode made no request at all** once its acquisition was shown (e.g. after Prepare Streaming, or with the
  scope stopped by `control_finn.py`): a `bazaar?stop` or another client was not noticed, and the lock state label
  was not refreshed (it showed LOCKED with the lock already off). In Single the page now polls every 1 s
  (`/get_client_id` check, then `GET /data`, which does not arm the scope). In Single an `AGAIN` answer starts the
  fast polling only while a Single click waits for its acquisition.
- Console message "Capture Lock: ended by , scope settings restored" (AUTO, unchecking Capture Lock): the reason is
  given.
- Mouse wheel on Ramp period / limits: the tau/f text below the field was not updated (only the `input` event did
  it); also for the PID, modulation and lock trigger fields.
- X+ of the plot range stopped at 10 s: it goes up to the longest window of the scope (68.72 s, decimation 524288).
- `py/lock_from_registers.py`: `--time 40s` gave `OverflowError` (5e9 ticks): the time is clamped to 0..2^32-1
  ticks (34.36 s) with a message, as in the page; `ns` and `µs` accepted. `--sw` limited to 0..15. Docstring: the
  `--sw` register is "Signal for trigger" of the page (`lock_lock_trig_sw`), not the scope Ext Trig (`lock_trig_sw`),
  options 6-8 are constant 0, and the note on the registers rewritten by the controller follows the fix above.
- `resources/remote_control/http_version/example_usage.py`: the Lock cell restores the lock-in and PID A of the
  `lock_mode` config (the Lock-in cell turned the modulation off and the PID cell left kp = ki = 0, so the level
  trigger never fired and the lock held nothing; `RESTORE_LOCK_MODE = False` prints a warning instead), and the cell
  "save data" ends with `rp.scope_auto()` (the script left the scope of the page in Single).
- `upload_app.sh`: the rw script of the OS as in the Makefile (`/opt/redpitaya/sbin/rw` in 2.0, `/boot/sbin/rw` in
  0.9x), `-w` removed `{index.html,js.css}` (now `js,css`), and `fpga.sh` gets the exec bit.

### Changed
- `c/streaming.c` closes the file descriptors inherited from the nginx worker (as `lock_in+pid_harmonic2` v2.4.3):
  `streaming` and `stream_tcp_osc_cmd` kept its sockets open while streaming. `c/stream_tcp_osc_cmd` runs with
  nice -10 and locked memory: at decimation 128 an ssh login or a loop forking on the board delayed it 11-16 ms
  (the scope buffer is 16.8 ms) and samples were lost. Not real time (at decimation 64 the loop never sleeps).
  `STREAM_NICE=<n>` in the environment changes the value (0: normal priority).
- AUTO: minimum window 1 us (was 100 ns). With only noise in the inputs (lock closed, ramp stopped) the "period" found
  in the noise gave 0...139 ns.
- Texts: labels of "Signal for trigger" 6-8 `0 (sqXo)`, `0 (sqYo)`, `0 (sqFo)` (showed code `/*sqXo */ 14'b0`);
  `ctrl_B` = "pidB_out + ramp_B" (said pidA_out) in `lock.v`, `fpga_lock.h`, `main.c`, `config_tool.py`; `src/fpga.h`
  `data_dec` 20 bits; `fpga/README.md` 20-bit decimation of the 2.0 scope; `resources/README.md`: a register is
  read with `name=` or `name`; `doc/lock_control.md`, `doc/Remote.md` (trigger registers written from outside).

### Added
- `test/minor_ui_sim.js` (wheel -> tau/f text, X+ up to 68.72 s, labels; 7 checks, the page of 2.3.17 fails 6).
- `test/lock_capture_ui_sim.js` part 7 (Single poll ~1 GET/s, fast only while a Single click waits, chain ended by
  Stop, console reason of the end of a capture; 6 checks); `test/config_load_window_sim.js` checks that no read-only
  parameter of `src/main.c` is sent; `test/auto_set_c_sim` parts 4 (trigger registers written from outside, 7 checks)
  and 5 (AUTO with noise, window >= 1 us).

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
