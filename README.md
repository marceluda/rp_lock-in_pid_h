# Red Pitaya Lock-in+PID Application with HARMONIC modulation

This started being a striped version of [lock-in+PID](https://github.com/marceluda/rp_lock-in_pid) project. Now it incorporated some new features that make it another App.


[![Example of usage](http://img.youtube.com/vi/330eYE75MYQ/0.jpg)](http://www.youtube.com/watch?v=330eYE75MYQ "Fast demosatration of usage")


## Features

- Lock-in amplifier
- in-phase and quadrature Demodulation
  - Demodulation for arbitrary phase
  - Demodulatión for double and triple frequency
- Two PID filters, for loop back stabilization
- Ramp/Scan controller for response analysis
- Lock control for automatic scan-stop / PID start
- Streaming system for continued acquisition of two channels
- Remote control through HTTP API
 

## Lock-in and PID application for RedPitaya environment

This is an application built for the [Red Pitaya STEMlab 125-14](https://www.redpitaya.com/) board (RP).
The board is closed-hardware and open-software. You can buy the board and build your own software.

If you have a RP board you can install the **Lock-in+PID** application
by copying the `lock_in+pid_harmonic` folder (that comes with this tar/zip file) to the
`/opt/redpitaya/www/apps` folder (inside the RP).

For more information about installing procedure, refer to:
https://marceluda.github.io/rp_lock-in_pid/TheApp/install/


# Development

To build of modify the App you need a linux development environment with:
  - Vivado 2015.2
  - gcc-linaro-4.9-2015.02-3-x86_64_arm-linux-gnueabihf (installed on `/opt/linaro/gcc-linaro-4.9-2015.02-3-x86_64_arm-linux-gnueabihf/`)


Run on terminal:

```bash
source settings.sh
make
```

Or form App folder `lock_in_mtm` :

```bash
source ../settings.sh
```


and then...

For web controller building:

```bash
make app
```

For FPGA implementation:

```bash
make fpga
```


For tar.gz packaging

```bash
make tar
```

For cleaning:

```bash
make clean       # clean all
make clean_app   # clean only C objects
make clean_fpga  # clean only FPGA implementation temp files and .bin
```


# Upload App to Red Pitaya device

UnZip / UnTar the App folder. Execute from terminal:

```bash
./upload_app.sh rp-XXXXXX.local
```

Replace `rp-XXXXXX.local` by your RP localname or IP address

Also, you can use your own SSH client and upload the lock_in+pid_harmonic folder the the
RedPiaya folder: `/opt/redpitaya/www/apps`
