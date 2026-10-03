# lock_in+pid_harmonic FPGA (Vivado 2020.1)

FPGA design of the App since v2.3.10, for the Red Pitaya **Ecosystem 2.0**
(STEMlab 125-14, Zynq 7010). It follows the structure of
[RedPitaya-FPGA](https://github.com/RedPitaya/RedPitaya-FPGA) (project `v0.94`,
model `Z10`) with the `lock` module of this App. The previous design
(Vivado 2015.2) is in `../fpga_old_2015.2/`.

## Build

Requires Vivado 2020.1 in `/tools/Xilinx/Vivado/2020.1` (or `VIVADO_SETTINGS=.../settings64.sh`).
The Makefile loads it by itself in a clean environment, so there is no need to
`source` anything (and it does not matter if Vivado 2015.2 is loaded).

```bash
make            # prj/v0.94/out/red_pitaya.bit + prj/v0.94/out/fpga.bit.bin (bootgen)
make project    # open the Vivado project (prj/v0.94/build/redpitaya.xpr) in the GUI
make clean
```

From the App folder (`..`), `make` builds the FPGA with this Makefile and copies
`red_pitaya.bit`, `fpga.bit` and `fpga.bit.bin` to the App. In Ecosystem 2.0
`fpga.sh` loads `fpga.bit.bin` with `fpgautil` (no device tree overlay is needed:
`controllerhf.so` accesses the registers through `/dev/mem`).

## Layout

```
Makefile                     make / make project / make clean
red_pitaya_vivado_Z10.tcl    Vivado script (RedPitaya-FPGA, + lock sources, no write_hw_platform)
synCheck.sh                  post-build report (timing, critical warnings)
brd/                         board files (redpitaya 1.1)
rtl/rtl/                     common RedPitaya RTL (rp_scope_com.v has the osc_ctrl_i input, see below)
sdc/red_pitaya.xdc           pin constraints
prj/v0.94/ip/system.tcl      PS block design (Zynq PS, XADC, ...)
prj/barebones/ip/ps7_config.tcl  PS7 configuration (sourced by system.tcl)
prj/v0.94/sdc/red_pitaya.xdc timing constraints
prj/v0.94/rtl/               top (red_pitaya_top.sv), PS wrapper, lock.v + lock/
prj/v0.94/out/               build products (bit, bin, reports, logs)
prj/v0.94/build/             Vivado project (generated)
```

## Register map (unchanged for the C controller)

| Address      | Block |
|--------------|-------|
| 0x40000000   | housekeeping (hk, 2.0 version) |
| 0x40100000   | oscilloscope (RedPitaya 2.0 `rp_scope_com`; inputs = lock `osc1`/`osc2`, external trigger = lock trigger) |
| 0x40200000   | (ASG removed) acknowledged, reads 0 |
| 0x40300000   | (PID removed) acknowledged, reads 0 |
| 0x40400000   | AMS / XADC |
| 0x40500000   | daisy chain |
| 0x40600000   | lock |

Differences with the RedPitaya v0.94 design, to behave as the 2015.2 design:

- DAC outputs = lock `out1`/`out2`; lock inputs = ADC (14 bit, 2's complement).
- The lock `osc_ctrl` drives the scope: bit 0/1 bypass the equalization filters,
  bit 2 + bits 19:3 override the decimation (streaming).
- Slow analog outputs: classic 250 MHz PWM driven by the lock (`pwm_cfg_a..d`).
- `exp_n_io[7]` = digital modulation, `exp_n_io[6]` = ramp direction (CAN TX if CAN is enabled).
- ASG/PID regions use `sys_bus_stub_ok` (no AXI error).
- `ip/ip/` of RedPitaya-FPGA (asg_dat_fifo, sync_fifo) is not included: only the ASG
  uses those IPs, and their tcl scripts are for Vivado 2025.1 (error IPS_TCL-100 in 2020.1).

The 2.0 scope differs from the 0.9x one in the trigger lock (0x94) and the 17-bit
decimation (max 64k): the C controller (`../src/fpga.c`) handles both.
