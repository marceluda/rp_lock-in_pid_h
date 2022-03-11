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
 

**New Interface for lock-in R & Phase** :


[![New iface](http://img.youtube.com/vi/DzSK8IQkUE4/0.jpg)](http://www.youtube.com/watch?v=DzSK8IQkUE4 "New R-phase interphase")


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


The App was based on code from project:
https://github.com/RedPitaya/RedPitaya/tree/release-v0.95/apps-free/scope

## Software requirements

You will need the following to build the Red Pitaya components:

1. Various development packages:

```bash
sudo apt-get install make u-boot-tools curl xz-utils nano
```

2. Xilinx [Vivado 2015.2](http://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/vivado-design-tools/2015-2.html) FPGA development tools. The SDK (bare metal toolchain) must also be installed, be careful during the install process to select it. Preferably use the default install location.

3. Linaro [ARM toolchain](https://releases.linaro.org/14.11/components/toolchain/binaries/arm-linux-gnueabihf/) for cross compiling Linux applications. We recommend to install it to `/opt/linaro/` since build process instructions relly on it.

```bash
TOOLCHAIN="http://releases.linaro.org/14.11/components/toolchain/binaries/arm-linux-gnueabihf/gcc-linaro-4.9-2014.11-x86_64_arm-linux-gnueabihf.tar.xz"
#TOOLCHAIN="http://releases.linaro.org/15.02/components/toolchain/binaries/arm-linux-gnueabihf/gcc-linaro-4.9-2015.02-3-x86_64_arm-linux-gnueabihf.tar.xz"
curl -O $TOOLCHAIN
sudo mkdir -p /opt/linaro
sudo chown $USER:$USER /opt/linaro
tar -xpf *linaro*.tar.xz -C /opt/linaro
```

**NOTE:** you can skip installing Vivado tools, if you only wish to compile user space software.

4. Missing `gmake` path

Vivado requires a `gmake` executable which does not exist on Ubuntu. It is necessary to create a symbolic link to the regular `make` executable.

```bash
sudo ln -s /usr/bin/make /usr/bin/gmake
```

5. On Ubuntu Linux you also need:

```bash
sudo apt-get install make u-boot-tools curl xz-utils
sudo apt-get install libx32gcc-4.8-dev
sudo apt-get install libc6-dev-i386
```

The building was tested on Ubuntu 16.04 Linux x86_64 


## Building



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
