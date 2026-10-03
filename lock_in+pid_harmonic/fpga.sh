#!/bin/sh
# v2.3.10: no streaming process of this App may read the PL while it is reprogrammed
D=/opt/redpitaya/www/apps/lock_in+pid_harmonic/c
PIDS=$(pidof $D/streaming $D/stream_tcp_osc_cmd 2>/dev/null)
if [ -n "$PIDS" ]; then
    kill -9 $PIDS 2>/dev/null
    sleep 0.2s
fi
rmdir /configfs/device-tree/overlays/Full 2> /dev/null
rm /tmp/loaded_fpga.inf 2> /dev/null
sleep 0.5s
/opt/redpitaya/bin/fpgautil -b /opt/redpitaya/www/apps/lock_in+pid_harmonic/fpga.bit.bin
