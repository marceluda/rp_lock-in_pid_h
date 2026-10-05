
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
