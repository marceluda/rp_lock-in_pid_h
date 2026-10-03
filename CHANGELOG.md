
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

v2.3.10
- same as v0.3.10 but with the FPGA design built with Vivado 2020.1 (RedPitaya-FPGA project
  structure): lock_in+pid_harmonic/fpga is now the RedPitaya-FPGA v0.94 project (model Z10,
  STEMlab 125-14) with the lock module; the Vivado 2015.2 design is kept in
  lock_in+pid_harmonic/fpga_old_2015.2 (to be removed)
- CHANGED fpga/Makefile: `make` builds red_pitaya.bit and fpga.bit.bin (bootgen), `make project`
  opens the Vivado project, `make clean`; Vivado 2020.1 is loaded inside the Makefile, isolated
  from the Vivado 2015.2 + Linaro environment used for the C controller
- CHANGED the oscilloscope is the RedPitaya 2.0 one (rp_scope_com): the C controller unlocks the
  trigger (register 0x94) before every acquisition and detects the end of the acquisition with
  conf bit 4 (it still works with the 0.9x scope)
- CHANGED the decimation of the 2.0 scope is widened to 20 bits in our copy of the FPGA
  (rp_scope_cfg / rp_scope_com / rp_decim: 40-bit accumulator, divider inputs pre-scaled by 16
  for decimations >= 64k), so the longest time range is again ~68 s (decimation 512k, as v0.3.4)
- FIXED scope samples: the 2.0 scope buffer returns the samples sign-extended to 16 bits; the C
  controller (conversion to volts, measurements, auto-set), c/osc, c/stream_tcp_osc_cmd and
  py/hugo.py keep the 14 ADC bits (still works with the 0.9x FPGA); streaming sends 14 bits as before
- FIXED c/lock parses unsigned registers with strtoul (stream_ip with the last octet >= 128 was
  rejected) and prints them unsigned; the UI sends stream_ip as unsigned and the controller
  does not overwrite stream_ip with its float echo; c/streaming IP buffer of 16 bytes
- FIXED /lock and /osc endpoints: `?name` without `=` reads the register (was a Lua error, 500);
  only register names and integers are passed to the shell
- FIXED a Single click made while another POST was in flight (e.g. right after switching the
  trigger mode to Single) was lost
- FIXED streaming stopped after a few seconds (c/stream_tcp_osc_cmd segfault): the send buffer
  could be overrun by up to send_min_len-1 samples; it is now flushed before a read that does not
  fit, has 2x margin, partial sends are completed and FPGA registers are read as volatile.
  c/streaming no longer polls stream_cmd at 100 % CPU (10 ms sleep)
- FIXED streaming sent repeated data (rate above the nominal one): the scope read data crossed
  to the PS clock without synchronization while it kept following the write pointer, which was
  sometimes read some samples behind and taken as a full turn of the buffer. FPGA: rp_scope_cfg
  holds the read data outside a read. c/stream_tcp_osc_cmd: the write pointer is read three
  times and used as a monotonic value, data is read up to WP-8, overruns, external resets/arms of
  the scope and a stopped write pointer (scope re-armed after 200 ms) are detected and logged
  to /tmp/lock_in+pid_harmonic_streaming.log; it sleeps when there is little data
- FIXED the first Start of the streaming sent no data: the controller no longer resets, arms or
  configures the scope while stream_cmd is set (pending changes are applied when it stops) and
  c/stream_tcp_osc_cmd re-arms the scope if the write pointer does not move
- FIXED E3 while streaming: c/streaming is started detached by c/stream_start.sh (it was an
  io.popen() never closed, the nginx worker blocked in pclose()); a new Prepare replaces the
  previous streaming processes; c/streaming ends when c/stream_tcp_osc_cmd ends
- FIXED leaving the App with the streaming active: rp_app_exit sets stream_cmd = 0 and stops
  c/streaming and c/stream_tcp_osc_cmd (SIGTERM, then SIGKILL) before returning, and fpga.sh
  kills them before loading the FPGA, so they never read the PL while it is reprogrammed
- FIXED Restart after a streaming left the scope frozen: the saved state restored stream_cmd = 1
  and the float echo of stream_ip (10.0.32.184 became 0.0.32.184). Transient commands
  (stream_cmd, lock now, launch lock trigger) are no longer saved and are forced to 0 by Restart
  and Config load; the streaming IP is saved as an exact integer and written with /lock?stream_ip=
- FIXED the last ~9000-16000 samples of each streaming were corrupted at Stop: c/stream_tcp_osc_cmd
  reads stream_cmd before and after each read of the buffer, drops a block read after it went to 0
  and ends by itself; the controller waits for it to end (50-500 ms) before reconfiguring the scope
- FIXED check_streaming alternated 0 and -1 while streaming (red status label): it now returns
  0/1 from the output of pidof (os.execute's status was lost to nginx's SIGCHLD handler)
- CHANGED streaming overruns are classified with the scope "samples written" counter: a reader
  more than half a buffer late is no longer taken as a bad write pointer read (wp_back, a whole
  buffer lost without notice) but read or, if more than a buffer late, the oldest samples are
  skipped (counted as overrun, "lost" samples logged); samples overwritten while being read are
  dropped. NOTE at decimation 64 (1.95 MS/s) the bus read of the PS is not enough (~1.63 MS/s
  measured): ~17 % of the samples are lost, now counted; decimation >= 128 is sustainable
- CHANGED the c/ tools are cross compiled by the App Makefile (`make c_tools`, part of `make all`
  and of the packages) with the flags of the original binaries (-g -std=gnu11
  -fstack-protector-strong), so they always match their sources
- FIXED time scale after Restart from the menu: the scale is saved in seconds and restored in the
  time units the server uses after the restart; the controller keeps the GUI xmin/xmax when a
  POST does not include them (ported from scope++ v1.1.1)
- NOTE the slow analog outputs AO0-AO3 are not driven by the lock module and exp_n_io[7]
  (digital_modulation) is always 0, as in the Vivado 2015.2 design (not changed)
- kept from the Vivado 2015.2 design: lock module at 0x40600000, scope at 0x40100000 with lock
  signals as inputs and lock trigger, filter bypass and streaming decimation controlled by the lock
  (osc_ctrl), slow analog outputs (PWM) driven by the lock, digital modulation / ramp direction
  outputs on exp_n_io[7:6], ASG (0x40200000) and PID (0x40300000) regions answered without error
