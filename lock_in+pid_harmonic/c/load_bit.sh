#!/bin/bash
# Load a bitstream into the FPGA (used by the nginx endpoint /lock_in+pid_harmonic/reload_fpga).
#   Ecosystem 0.9x/1.0: /dev/xdevcfg exists -> write the .bit file there (original behaviour).
#   Ecosystem 2.0     : no /dev/xdevcfg      -> NOT supported, the FPGA is not touched (exit 2).
#     Reprogramming the PL (overlay rmdir + fpgautil) while controllerhf.so and /data access it
#     over AXI hangs the bus and the watchdog reboots the board. In 2.0 the FPGA is loaded by the
#     App's fpga.sh when the App starts: restart the App to reload it.

if [ $# -ne 1 ]
then
    echo "No arguments supplied"
    exit 1
fi

if [ -e /dev/xdevcfg ]
then
    if test -f "$1"; then
        echo "$1 exists."
        cat <"$1"  > /dev/xdevcfg
    else
        echo "$1 not found."
        exit 1
    fi
else
    echo "reload_fpga not supported on Ecosystem 2.0: restart the App (bazaar stop/start) to reload the FPGA"
    exit 2
fi
