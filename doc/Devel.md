# Development: building and modifying the App

How to build, modify, test and install `lock_in+pid_harmonic` v2.3.24 (branch `master`). The internal
structure is explained in [Structure.md](Structure.md) and the registers in [FPGA.md](FPGA.md).

- [Source tree](#source-tree)
- [Software requirements](#software-requirements)
- [Building everything](#building-everything)
- [Makefiles and targets](#makefiles-and-targets)
- [C controller (`controllerhf.so`)](#c-controller-controllerhfso)
- [Tools of `c/` (`lock`, `osc`, streaming)](#tools-of-c-lock-osc-streaming)
- [FPGA (Vivado 2020.1)](#fpga-vivado-20201)
- [Web interface (`index.html`)](#web-interface-indexhtml)
- [Registers and `config_tool.py`](#registers-and-config_toolpy)
- [Simulations and tests (`test/`)](#simulations-and-tests-test)
- [Installing on the board](#installing-on-the-board)
- [Versioning and packages](#versioning-and-packages)

## Source tree

```
rp_lock-in_pid_h/
├── Makefile                 # all = App build + zip + tar into archive/
├── settings.sh              # environment for the C build (Vivado 2015.2 + Linaro)
├── _build_number            # BUILD_NUMBER=N (incremented by make clean_*), not versioned
├── README.md  CHANGELOG.md  CITATION.cff  LICENSE (GPL-3.0)
├── doc/                     # this documentation
├── archive/                 # built packages (*.zip, *.tar.gz), not versioned
├── resources/
│   ├── config_tool.py       # register table -> code generator (see below)
│   ├── doc_tool.py
│   ├── remote_control/http_version/   # control_finn.py, example_usage.py (HTTP API client)
│   ├── remote_control/shh_version/    # SSH client (deprecated)
│   ├── streaming/           # TCP receiver for the streaming (server.c, read_bin.py)
│   ├── process_web_download/, rp_cmds/, code_helpers/ (muxer generator, sin/cos tables)
│   └── README.md            # streaming and remote control notes
└── lock_in+pid_harmonic/    # the App (this folder is what is installed on the board)
    ├── Makefile             # controller, c tools, FPGA, target/, zip, tar, upload
    ├── index.html           # web interface (HTML + JS in one file)
    ├── css/  js/            # styles, jquery.mousewheel, js.cookie
    ├── info/info.json       # name and version shown by the Ecosystem; icon.png
    ├── nginx.conf           # extra HTTP endpoints (Lua): /lock, /osc, /streaming, ...
    ├── fpga.sh              # Ecosystem 2.0: loads fpga.bit.bin with fpgautil when the App starts
    ├── fpga.conf            # path of the .bit (Ecosystem 0.9x)
    ├── fpga.bit.bin, red_pitaya.bit, fpga.bit   # FPGA images (built)
    ├── controllerhf.so      # C controller (built, versioned)
    ├── src/                 # C controller sources
    │   ├── main.c / main.h  # parameter table, rp_set_params / rp_get_params / rp_get_signals
    │   ├── worker.c / .h    # scope worker thread, auto-set, measurements
    │   ├── fpga.c / fpga.h  # scope registers (0x40100000)
    │   ├── lock.c / .h, fpga_lock.c / .h   # lock registers (0x40600000)
    │   ├── calib.c, generate.c, fpga_awg.c, pid.c, fpga_pid.c   # from the original scope App
    │   └── Makefile
    ├── c/                   # tools run on the board: lock, osc, streaming, stream_tcp_osc_cmd
    │   ├── *.c, Makefile, lock.txt, osc.txt, load_bit.sh, stream_start.sh
    ├── py/                  # Python scripts run on the board (hugo.py, lock_from_registers.py, ...)
    ├── fpga/                # FPGA project (Vivado 2020.1, RedPitaya-FPGA structure)
    │   ├── Makefile  README.md  red_pitaya_vivado_Z10.tcl  synCheck.sh
    │   ├── rtl/rtl/         # common Red Pitaya RTL (classic/rp_scope_*.v modified by this App)
    │   ├── prj/v0.94/rtl/   # red_pitaya_top.sv, red_pitaya_ps.sv, lock.v, lock/*.v
    │   ├── prj/v0.94/{ip,sdc}, prj/barebones/ip, sdc/, brd/
    │   └── prj/v0.94/out/   # build products (not versioned)
    ├── doc/                 # design notes: lock_control.md, lock_capture.md (+ Doxygen setup)
    ├── test/                # simulations (xsim, node, native C)
    ├── upload_app.sh        # upload a package to a board through SSH
    └── target/              # staging folder for the packages (built, not versioned)
```

## Software requirements

| Tool | Version | Used for | Path on the development PC |
|---|---|---|---|
| Xilinx Vivado | **2020.1** | FPGA (synthesis, implementation, `bootgen`, xsim) | `/tools/Xilinx/Vivado/2020.1` (`VIVADO_SETTINGS`) |
| Xilinx Vivado (SDK) | 2015.2 | environment of the C build (`settings.sh`) | `/opt/Xilinx/Vivado/2015.2` |
| Linaro ARM toolchain | gcc-linaro-4.9-2015.02-3 (or 2014.11) `arm-linux-gnueabihf` | cross compiling the controller and the `c/` tools | `/opt/linaro/` |
| GNU make, zip, tar, sed | — | build and packaging | — |
| node.js | any recent (v22 used) | UI simulations in `test/` | — |
| gcc (PC) | — | `test/auto_set_c_sim` | — |
| Python 3 + numpy | — | `resources/config_tool.py`, remote control | — |

The Vivado 2015.2 installation is only needed because `settings.sh` sources it; the C code is compiled
with the Linaro toolchain (`CROSS_COMPILE=arm-linux-gnueabihf-`). Installation notes (kept from the README
of the 0.3.x series, tested on Ubuntu 16.04 at the time):

```bash
# development packages
sudo apt-get install make u-boot-tools curl xz-utils nano zip
# Linaro toolchain in /opt/linaro (settings.sh looks for 2015.02-3 or 2014.11)
TOOLCHAIN="http://releases.linaro.org/15.02/components/toolchain/binaries/arm-linux-gnueabihf/gcc-linaro-4.9-2015.02-3-x86_64_arm-linux-gnueabihf.tar.xz"
#TOOLCHAIN="http://releases.linaro.org/14.11/components/toolchain/binaries/arm-linux-gnueabihf/gcc-linaro-4.9-2014.11-x86_64_arm-linux-gnueabihf.tar.xz"
curl -O $TOOLCHAIN
sudo mkdir -p /opt/linaro && sudo chown $USER:$USER /opt/linaro
tar -xpf *linaro*.tar.xz -C /opt/linaro
# Vivado needs a gmake executable
sudo ln -s /usr/bin/make /usr/bin/gmake
# 32-bit libraries needed by old toolchains on 64-bit Ubuntu
sudo apt-get install libc6-dev-i386
```

Vivado 2015.2 (with the SDK) and Vivado 2020.1 are installed from the Xilinx installers. Only the C part
needs the 2015.2 environment; to build only user-space software Vivado is not needed if `settings.sh` is
adapted (it sources `/opt/Xilinx/Vivado/2015.2/settings64.sh`).

Load the C environment:

```bash
cd rp_lock-in_pid_h
source settings.sh          # sources /opt/Xilinx/Vivado/2015.2/settings64.sh, adds Linaro to PATH,
                            # exports TOOLCHAIN_PATH and CROSS_COMPILE=arm-linux-gnueabihf-
```

The FPGA Makefile loads Vivado 2020.1 by itself in a clean environment (`env -i`), so it does not matter
whether `settings.sh` was sourced: both environments never mix.

## Building everything

```bash
cd rp_lock-in_pid_h
source settings.sh
LANG=C make
```

This builds the controller, the `c/` tools and, if any FPGA source changed, the FPGA (about 30 min), then
`target/` and the packages `archive/lock_in+pid_harmonic-<version>-<build>-devbuild.{zip,tar.gz}`.

A typical rebuild after changing only C or the web page (as devAgent does, FPGA untouched):

```bash
source settings.sh
make -C lock_in+pid_harmonic clean_app && LANG=C make
```

`clean_app` and `clean_fpga` increment the build number in `_build_number`.

## Makefiles and targets

Root `Makefile`:

| Target | Action |
|---|---|
| `make` / `make all` | `make -C lock_in+pid_harmonic all zip tar` (packages in `archive/`) |
| `make clean` | `make -C lock_in+pid_harmonic clean` |
| `make upload` | `make -C lock_in+pid_harmonic upload` |

`lock_in+pid_harmonic/Makefile`:

| Target | Action |
|---|---|
| `all` | `controllerhf.so` + `c_tools` + `fpga` |
| `app` | `controllerhf.so` + `c_tools` |
| `controllerhf.so` | builds three variants of the controller: `controllerhf_dbg.so` (DEBUG on), `controllerhf_rld.so` (RELOAD dock) and `controllerhf.so` (the one packaged), editing `src/main.h` / `src/main.c` with `sed` between builds |
| `c_tools` | `make -C c all` (cross compiled `lock`, `osc`, `streaming`, `stream_tcp_osc_cmd`) |
| `fpga` | `red_pitaya.bit` (from `fpga/`), `fpga.bit` (copy) and `fpga.bit.bin` (bootgen) |
| `target/lock_in+pid_harmonic` | staging of the installable folder (also copies `upload_app.sh`, `resources/`, README, CHANGELOG; sets the version in `info.json` and `index.html`; removes `__pycache__`/`*.pyc`) |
| `zip`, `tar` | packages in `../archive/` |
| `clean`, `clean_app`, `clean_fpga`, `clean_target` | clean all / C (`src`, `c`, `*.so`, target) / FPGA / target |
| `upload`, `upload_bit`, `upload_html`, `upload_py` | copy to the board by SSH (needs `RPIP`, on the command line or in `../_settings.env`, see below; `check_rpip` stops if it is empty). Since v2.3.15 they depend only on `target/` (`upload_html` sends the `index.html` of `target/`, with the version), make the file system writable with the `rw` script of the OS (`/opt/redpitaya/sbin/rw` with `PATH_REDPITAYA` exported on 2.0, `/boot/sbin/rw` on 0.9x), `upload` keeps `fpga.sh` at 755 and `upload_bit` also sends `fpga.bit.bin`. Never run by the build |

`lock_in+pid_harmonic/fpga/Makefile`: see [FPGA](#fpga-vivado-20201).

Settings file `_settings.env` (root, not versioned), read by both Makefiles:

```make
RPIP=rp-XXXXXX.local
RPOPTS=-l root -p 22
RPSCP=-P 22
```

## C controller (`controllerhf.so`)

- Sources in `lock_in+pid_harmonic/src/`, `src/Makefile`: `$(CROSS_COMPILE)gcc`, `-Wall -Werror -g -fPIC`,
  linked with `-shared -lm -lpthread`; `VERSION` and `REVISION` come from `info/info.json` and the build
  number through `CFLAGS`.
- Build: `make -C lock_in+pid_harmonic controllerhf.so` (with `settings.sh` loaded). The files
  `src/main_controllerhf.so_.c` and `src/main_controllerhf_rld.so_.c` are copies left by the Makefile.
- To install a new `.so` on a running board: copy it and **stop + start the App**
  (`/bazaar?stop=` then `/bazaar?start=lock_in+pid_harmonic`), so that nginx loads the new library.
- Debug output (`TRACE`) goes to the nginx log when built with `DEBUG` (`controllerhf_dbg.so`).

## Tools of `c/` (`lock`, `osc`, streaming)

| Tool | Source | Purpose |
|---|---|---|
| `lock` | `c/lock.c` | read/write the lock registers by name (`/lock_in+pid_harmonic/lock`) |
| `osc` | `c/osc.c` | read/write the scope registers by name, `dump` of both buffers (`/lock_in+pid_harmonic/osc`) |
| `streaming` | `c/streaming.c` | waits for `stream_cmd`, launches `stream_tcp_osc_cmd` (`/lock_in+pid_harmonic/streaming`, through `stream_start.sh`) |
| `stream_tcp_osc_cmd` | `c/stream_tcp_osc_cmd.c` | reads the scope buffers continuously and sends them over TCP: `stream_tcp_osc_cmd <host> <port> <send_min_len>` |

**From the development PC (cross compilation, since v2.3.10).** `c/Makefile` uses `$(CROSS_COMPILE)gcc`
with its own flags (`-g -std=gnu11 -fstack-protector-strong`, plus `-Wno-overflow` for `lock`/`osc`), the
same as the original binaries built on the board, independent of the `CFLAGS` of the App Makefile:

```bash
cd rp_lock-in_pid_h
source settings.sh                       # CROSS_COMPILE=arm-linux-gnueabihf-
make -C lock_in+pid_harmonic c_tools     # or: make -C lock_in+pid_harmonic/c all
make -C lock_in+pid_harmonic/c clean
```

`make all`, `make app` and the packages include `c_tools`, so the binaries in `target/` always match their
sources. Extra flags: `make -C lock_in+pid_harmonic/c EXTRA_CFLAGS=-Wall`.

**On the board (as before v2.3.10).** With `CROSS_COMPILE` empty the same Makefile uses the native `gcc`:

```bash
ssh root@rp-XXXXXX.local
export PATH_REDPITAYA=/opt/redpitaya; /opt/redpitaya/sbin/rw     # read-write file system (Ecosystem 2.0)
cd /opt/redpitaya/www/apps/lock_in+pid_harmonic/c
make clean && make all
```

The original binaries were built with gcc 5.4 on a 0.9x board. Whether RedPitaya_OS 2.04 still ships
`gcc` and `make` has **not been checked (a confirmar)**; cross compilation is the supported way.

## FPGA (Vivado 2020.1)

`lock_in+pid_harmonic/fpga/` follows the structure of
[RedPitaya-FPGA](https://github.com/RedPitaya/RedPitaya-FPGA) (project `v0.94`, model `Z10`), with the
`lock` module of the App. Details: `fpga/README.md`.

```bash
cd rp_lock-in_pid_h/lock_in+pid_harmonic/fpga
make            # prj/v0.94/out/red_pitaya.bit + prj/v0.94/out/fpga.bit.bin (bootgen)
make bit        # only the bitstream
make bin        # only fpga.bit.bin from an existing red_pitaya.bit
make project    # create prj/v0.94/build/redpitaya.xpr and open it in the Vivado GUI (no synthesis)
make clean      # remove the build products of PRJ
make help
```

Variables: `VIVADO_SETTINGS` (default `/tools/Xilinx/Vivado/2020.1/settings64.sh`), `PRJ` (`v0.94`),
`MODEL` (`Z10`), `DEFINES`. Any change in `rtl/`, `prj/v0.94/{rtl,ip,sdc}`, `sdc/`, `brd/` or the tcl
rebuilds the bitstream. After a build `synCheck.sh` writes a report (timing, critical warnings) to
`prj/v0.94/out/`; the log is `prj/v0.94/out/vivado.log`.

From the App folder, `make fpga` builds through this Makefile and copies `red_pitaya.bit`, `fpga.bit` and
`fpga.bit.bin` to the App. On Ecosystem 2.0 only `fpga.bit.bin` is used (by `fpga.sh`).

Where to change things:

| What | File |
|---|---|
| Lock module (registers, muxers, lock-in, outputs) | `prj/v0.94/rtl/lock.v` (bus decoder generated by `config_tool.py`) |
| Submodules (PID, filters, generator, ramp, lock control) | `prj/v0.94/rtl/lock/*.v`; tables of the generator `lock/data_*_ss.dat` (`resources/code_helpers/gen_sin_cos.py`) |
| Connections to ADC/DAC/scope/PWM/DIO | `prj/v0.94/rtl/red_pitaya_top.sv` |
| Scope (decimation, `osc_ctrl_i`, bus read) | `rtl/rtl/classic/rp_scope_com.v`, `rp_scope_cfg.v`, `rp_decim.v` |
| Constraints | `sdc/red_pitaya.xdc`, `prj/v0.94/sdc/` |

Known: timing does not fully close; the App works. The timing of the v2.3.23 image (new `lock_ctrl.v`) is not in the
CHANGELOG (**a confirmar**). v2.3.20: WNS −0.888 ns, TNS −217.4 ns (762 endpoints; the
references reach the lock-in 1 clock later than the outputs, so that the phase through the DAC is the one of v2.3.18).
v2.3.19: WNS −1.099 ns, TNS −207.5 ns (774 endpoints) after
adding pipeline registers to the lock-in, PIDs, generator and outputs ([`lock_latency.md`](../lock_in+pid_harmonic/doc/lock_latency.md));
v2.3.17: WNS −8.954 ns, TNS −9565 ns (v2.3.15: −10.035 / −8637), the worst paths were the long combinational paths of
the loop (PID → scope muxes, outputs). If you add logic between two registers of the loop, keep it short (8 ns) or
add a register and document its latency; the bus read of the lock module meets timing (+1.892 ns) with the 2-cycle multicycle constraint
of `prj/v0.94/sdc/red_pitaya.xdc` l. 82-83 (CHANGELOG v2.3.17, `devAgent.md`). If you add a register to the read
mux of `lock.v`, keep it a register of `adc_clk` held during `sys_ren` (as the `*_rd` copies), or the multicycle
constraint is no longer valid ([FPGA.md](FPGA.md#lock-module-0x40600000)). Simulations of `lock_ctrl.v` and of
the bus reads: see [test/](#simulations-and-tests-test).

## Web interface (`index.html`)

- Everything (HTML, CSS overrides, JavaScript) is in `index.html`; it uses jQuery, Bootstrap and Flot from
  the Ecosystem (`../assets/`) and `js/jquery.mousewheel.js`, `js/js.cookie.min.js` of the App.
- The version shown in the title is set when packaging (`var app_version = 'VERSION'` is replaced in
  `target/`): test with the file from `target/`, not from the source folder.
- To try a change on the board without rebuilding the rest, copy `index.html` (and `js/`, `css/`) to
  `/opt/redpitaya/www/apps/lock_in+pid_harmonic/` (`upload_app.sh -w <host>` does it) and reload the page;
  `nginx.conf` serves `index.html` with `Cache-Control: no-cache`.
- Syntax check: extract the scripts and run `node --check` (as devAgent does), and run the node
  simulations of `test/`, which load the functions of `index.html`.
- Blocks marked with comments like `[LOCK CAPTURE BEGIN]` / `[TRIG FROM GRAPH BEGIN]` are used by the
  simulations; keep the markers.

## Registers and `config_tool.py`

`resources/config_tool.py` keeps the list of the lock registers (name, width, sign, reset value,
description, UI widget) and of the scope registers, and regenerates the code between "dock" markers:

| Output | Docks |
|---|---|
| `fpga/prj/v0.94/rtl/lock.v` | `[WIREREG DOCK]`, `[FPGA MEMORY DOCK]` |
| `src/fpga_lock.h`, `src/lock.c`, `src/main.c`, `src/main.h` | register struct, `[FPGAUPDATE DOCK]`, `[MAINDEFH DOCK]`, parameter table |
| `index.html` | fields and selectors |
| `c/lock.c`, `c/osc.c`, `c/lock.txt`, `c/osc.txt` | `[LOCKREGS DOCK]`, `[OSCREGS DOCK]`, CSV files |
| `py/hugo.py` | register tables |

Usage (from inside `rp_lock-in_pid_h/`): `python3 resources/config_tool.py` (verilog, main, html, py), or
with arguments `verilog|fpga`, `main`, `html`, `py`, `rp_c`, `all`, `clean`. Each run moves the modified
files to `name_YYYYMMDD_HHmmss.ext` backups. Hand-written blocks inside a dock (e.g. the `c_block` of
`lock_control` in `[FPGAUPDATE DOCK]`) are kept in the table of the tool; review the diff after running it.
Updated for the v0.94 tree in v2.3.13; v2.3.15: `index=` of each register (for `TrgUnlock`, index 37 of the
scope) and the ranges of `lock.txt`/`osc.txt`; v2.3.17: the generated read mux of `lock.v` uses the `*_rd` copies
and loads `sys_rdata` only on reads. **The `html` output is out of date** (its `input_buttons` list is the one of
v2.3.13): `index.html` has been edited by hand since v2.3.15, do not regenerate it (`devAgent.md`, 2026-10-09 12:14).

After adding or changing a register: run the tool, rebuild FPGA + controller + tools, and update
[FPGA.md](FPGA.md).

## Simulations and tests (`test/`)

| Test | Command | What it checks |
|---|---|---|
| `lock_ctrl_tb.v` | `test/lock_ctrl_sim.sh [work_dir]` (Vivado 2020.1 xsim) | the lock state machine `lock_ctrl.v`; prints `TB RESULT: PASS` |
| `lock_ctrl_ui_sim.js` | `node test/lock_ctrl_ui_sim.js` | UI ↔ controller ↔ FPGA model of the lock control (v2.3.13) |
| `lock_capture_ui_sim.js` | `node test/lock_capture_ui_sim.js` | Capture Lock, Fire on click, restore, AUTO (v2.3.14) |
| `trig_from_graph_sim.js` | `node test/trig_from_graph_sim.js` | click → time conversion of *Choose from graph* (v2.3.12) |
| `trig_input_units_sim.js` | `node test/trig_input_units_sim.js [--old]` | Time / Level trigger fields with units, empty fields not sent as 0 (v2.3.16) |
| `lock_bus_read_tb.sv` | `test/lock_bus_read_sim.sh [work_dir [lock.v]]` (Vivado 2020.1 xsim) | bus reads of `lock.v` through `sys_bus_cdc` with asynchronous clocks: `sys_rdata` stable when the PS takes it (v2.3.17); prints `TB RESULT: PASS` |
| `config_load_window_sim.js` | `node test/config_load_window_sim.js [--old]` | Config → load of the time window: conversion, and the real chunked send of `index.html` against a model of `rp_set_params()` (forceX handshake) plus a GET poll (v2.3.17) |
| `config_load_block_sim.js` | `node test/config_load_block_sim.js [index.html]` | the option "Don't turn on PIDs and Ramp on config loading": unchecked by default, Config → load and Restart restore ramp / Scan enable / PIDs as saved, checked keeps them off, lock requests always 0 (v2.3.26, 10 checks) |
| `lock_latency_tb.sv` | `test/lock_latency_sim.sh [work_dir [old_ref]]` (Vivado 2020.1 xsim) | `lock.v` of the working tree side by side with the one of a commit (default v2.3.18): every signal is the old one delayed by the latency of [`lock_latency.md`](../lock_in+pid_harmonic/doc/lock_latency.md), bit by bit (v2.3.19); prints `TB RESULT: PASS` |
| `auto_set_c_sim/` | `test/auto_set_c_sim/run.sh [src dir]` | the real C controller compiled for the PC with fake `/dev/mem` (`fake_hw.h`, `harness.c`): AUTO after a capture, forceX; since v2.3.23 also a model of the circular scope buffer and of the lock pulse (slow windows, Capture Lock with history, time trigger after a stopped ramp); since v2.3.26 section 10: Auto waits for the trigger, forced after its time limit (`SIM_AUTO=1` runs only it) |
| `minor_ui_sim.js` | `node test/minor_ui_sim.js [index.html]` | wheel → τ/f text, X+ up to 68.72 s, labels (v2.3.18) |
| `ramp_mod_period_tb.v` | `test/ramp_mod_period_sim.sh [work_dir]` (Vivado 2020.1 xsim) | periods of the ramp floor/ceil triggers and of the harmonic modulation trigger on the RTL, the formulas used by Reset zoom (v2.3.21); prints `TB RESULT: PASS` |
| `reset_zoom_sim.js` | `node test/reset_zoom_sim.js [index.html] [--old]` | the real `resetZoom()` against a model of the time range code of `src/main.c` (v2.3.21; 0.98 × T and trace clearing since v2.3.23) |
| `plot_wheel_sim.js` | `node test/plot_wheel_sim.js [index.html]` | mouse wheel on the plot: no key / SHIFT / ALT, limits, debounce, Capture Lock (v2.3.22) |
| `osc_presets_sim.js` | `node test/osc_presets_sim.js [index.html]` | the OscA\|OscB presets, the `usr` dialog and the Ext Trig → Trigger panel rule (v2.3.24) |

Run them from `lock_in+pid_harmonic/`. All exit with code 1 on failure. `--old` runs a check against the code of
the previous version (it must fail). `lock_ctrl_tb.v` covers 32-bit time triggers ≥ 2³¹ since v2.3.15 (cases
14-15). Results of v2.3.17 (`devAgent.md`, `build_logs/rp_lock-in_pid_h_20261009_2124_v2317c_sim.txt`):
`lock_ctrl_sim` 35/35, `lock_bus_read_sim` PASS (0 unstable reads of 4000), `lock_ctrl_ui_sim` 28/28,
`lock_capture_ui_sim` 63/63, `trig_input_units_sim` 38/38, `trig_from_graph_sim` 0 failures,
`config_load_window_sim` 21/21; `auto_set_c_sim` 14/14 (v2.3.15). Counts reported in the CHANGELOG for later
versions: `lock_ctrl_sim` 45/45, `auto_set_c_sim` 44/44, `lock_capture_ui_sim` 79/79, `reset_zoom_sim` 29/29 (v2.3.23);
`plot_wheel_sim` 59 checks (v2.3.22); `ramp_mod_period_sim` 10 checks (v2.3.21); `minor_ui_sim` 7 checks (v2.3.18);
`osc_presets_sim` 37 checks (v2.3.24). A full run of all the tests on 2.3.24 is **a confirmar** (not in this page's sources).

The Python client `control_finn.py` was tested by devAgent against a fake HTTP server of the board (Lua argument
order, `c/lock`/`c/osc`, 2.0 scope with trigger lock, a model of the C worker, `/data` that only answers a body
sent with the headers). Those scripts are not in the repository (devAgent scratchpad); the board tests are in
`reportes/lock-in_pid_h.md`.

On the board the reference test is the LOCK MODE procedure of `test_files/lock_test.md` (Apps root),
with `dummy_simulator` on a second board; reports in `reportes/lock-in_pid_h_lock_test/`.

## Installing on the board

From a package (`archive/*.tar.gz` or `.zip`, or a GitHub release):

```bash
tar -xzf lock_in+pid_harmonic-2.3.24-<build>-devbuild.tar.gz
./upload_app.sh rp-XXXXXX.local          # -p <ssh port>; -w uploads only index.html, js, css
```

`upload_app.sh` installs an SSH key if needed, makes the file system writable (`/boot/sbin/rw`), replaces
`/opt/redpitaya/www/apps/lock_in+pid_harmonic/` and copies the App. By hand: copy the folder
`lock_in+pid_harmonic/` of the package (not the source folder) to `/opt/redpitaya/www/apps/` with the
file system in read-write mode, keeping `fpga.sh` executable (755).

After installing: open the App page, or stop + start it (`/bazaar?stop=`, `/bazaar?start=lock_in+pid_harmonic`)
if an older version was running. If `nginx.conf` changed, restart nginx
(`systemctl restart redpitaya_nginx`). On Ecosystem 2.0 `reload_fpga` is not supported: restarting the App
reloads the FPGA.

Notes for Ecosystem 2.0 (`testAgent.md`):

- In a non-interactive SSH, `rw` needs `PATH_REDPITAYA`: `export PATH_REDPITAYA=/opt/redpitaya; /opt/redpitaya/sbin/rw`.
  The `upload*` targets of the Makefile do so since v2.3.15, and `upload_app.sh` since v2.3.18 (l. 117-119:
  `/opt/redpitaya/sbin/rw` on Ecosystem 2.0, `/boot/sbin/rw` on 0.9x).
- Each `POST /data` (page, `curl`, `control_finn.py`) leaves an open connection in the nginx of the board; after
  long test sessions restart it with `systemctl restart redpitaya_nginx` (then start the App again)
  ([Remote.md](Remote.md#known-issue-of-the-ecosystem-post-data-leaves-connections-open)).
- Close any browser tab with the main menu of the board before testing: it can relaunch the main menu and
  unload the App.

## Versioning and packages

- Version: `lock_in+pid_harmonic/info/info.json` (`"version": "2.3.24-BUILD_NUMBER"`), `CHANGELOG.md`, `README.md`
  ("Current version"). Since v2.3.19 the build writes the version of `info.json` in `<title>` and in the page title
  of `target/…/index.html` (Makefile l. 101-102); the title in the source `index.html` may be older (2.3.22 now) and
  does not matter. Build number: `_build_number`.
  Revision: `REVISION` (default `devbuild`).
- Package name: `lock_in+pid_harmonic-<VER>-<BUILD_NUMBER>-<REVISION>.{zip,tar.gz}` in `archive/`.
- Branches: since 2026-10-15 `master` is the 2.3.x line (FPGA Vivado 2020.1, Ecosystem 2.0); the 0.3.x series
  (FPGA Vivado 2015.2, 0.9x / 1.0 ecosystems) stays in the tags `v0.3` .. `v0.3.11`. Tags `v2.3.11` .. `v2.3.24`.
  `devel2.0` is left as it was (up to its last commit) and is no longer used.
