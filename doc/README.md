# RP Lock-in+PID Harmonic — documentation

Documentation of `lock_in+pid_harmonic` **v2.3.24** (branch `master`, Ecosystem 2.0, FPGA built with
Vivado 2020.1). Back to the [project README](../README.md) · [CHANGELOG](../CHANGELOG.md).

| Document | Contents |
|---|---|
| [App.md](App.md) | The instruments of the App and their technical data: frequencies, filters, gains, ranges, time spans, measured lock performance |
| [Usage.md](Usage.md) | The web interface panel by panel, and the procedures: scan, lock-in, close and check a lock, configs |
| [Structure.md](Structure.md) | How the web page, the server (nginx + `controllerhf.so`) and the FPGA work together; block diagrams of the FPGA |
| [FPGA.md](FPGA.md) | Register map of the lock module and of the oscilloscope, bit fields and selector values |
| [Remote.md](Remote.md) | Remote control over HTTP (`/lock`, `/osc`, `/data`) with Python (`control_finn.py`) examples; known issue of `POST /data`; tools and scripts on the board |
| [Devel.md](Devel.md) | Source tree, requirements, building (C, `c/` tools, FPGA), tests, installation |

Design notes kept with the sources (`lock_in+pid_harmonic/doc/`):

- [`lock_control.md`](../lock_in+pid_harmonic/doc/lock_control.md): the lock control of v2.3.13
  (`lock_control` / `lock_status`, state machine in the FPGA, locking from Python).
- [`lock_capture.md`](../lock_in+pid_harmonic/doc/lock_capture.md): *Capture Lock* and *Fire on click* (v2.3.14).

The register table that this file had before (a copy of `lock_in+pid_harmonic/c/lock.txt`) is now
[FPGA.md](FPGA.md), checked against the RTL.

Screenshots of the web interface are in the hidden folder `.Usage/`, and the figures of the remote control in `.Remote/`.
