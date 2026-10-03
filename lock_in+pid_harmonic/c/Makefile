# Helper tools of the App (run on the Red Pitaya from py/ and src/).
# Cross compiled from the App Makefile (`make c_tools`, part of `make all`) with the
# Linaro toolchain of ../../settings.sh (CROSS_COMPILE=arm-linux-gnueabihf-).
# On the board itself (CROSS_COMPILE empty) it uses the native gcc, as originally.

CC = $(CROSS_COMPILE)gcc
RM = rm

# Same flags as the binaries of 9c5139f (native gcc 5.4 on the board: GNU C11, -g, no -O,
# default -fstack-protector-strong). Independent of the CFLAGS exported by the App Makefile.
TOOLS_CFLAGS = -g -std=gnu11 -fstack-protector-strong $(EXTRA_CFLAGS)

TOOLS = lock osc streaming stream_tcp_osc_cmd

all: $(TOOLS)

lock: lock.c
	$(CC) -o $@ $< $(TOOLS_CFLAGS) -Wno-overflow

osc: osc.c
	$(CC) -o $@ $< $(TOOLS_CFLAGS) -Wno-overflow

streaming: streaming.c
	$(CC) -o $@ $< $(TOOLS_CFLAGS)

stream_tcp_osc_cmd: stream_tcp_osc_cmd.c
	$(CC) -o $@ $< $(TOOLS_CFLAGS)

clean:
	-$(RM) -f $(TOOLS)

.PHONY: all clean
