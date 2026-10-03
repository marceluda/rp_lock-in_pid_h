#!/bin/sh
# lock_in+pid_harmonic v2.3.10: starts c/streaming detached from nginx.
# Called by the /lock_in+pid_harmonic/streaming location of nginx.conf ("Prepare Streaming").
# Before, nginx ran it with io.popen() and never closed the pipe: when Lua's garbage collector
# closed it, the nginx worker blocked in pclose() until the streaming ended (E3, /data and Stop
# of the UI not answering). Here the process gets its own session, no pipe to nginx, and this
# script returns at once.
D=/opt/redpitaya/www/apps/lock_in+pid_harmonic/c
LOG=/tmp/lock_in+pid_harmonic_streaming.log

# Only one instance: a previous "Prepare" (maybe with another IP/port) is replaced.
# stream_tcp_osc_cmd runs in its own process group, so it is stopped explicitly too.
PIDS=$(pidof $D/streaming $D/stream_tcp_osc_cmd)
if [ -n "$PIDS" ]; then
    kill $PIDS 2>/dev/null
    i=0
    while [ $i -lt 10 ] && [ -n "$(pidof $D/streaming $D/stream_tcp_osc_cmd)" ]; do
        sleep 0.1; i=$((i+1))
    done
    PIDS=$(pidof $D/streaming $D/stream_tcp_osc_cmd)
    [ -n "$PIDS" ] && kill -9 $PIDS 2>/dev/null
fi

if command -v setsid >/dev/null 2>&1; then
    setsid $D/streaming > $LOG 2>&1 < /dev/null &
else
    nohup  $D/streaming > $LOG 2>&1 < /dev/null &
fi
exit 0
