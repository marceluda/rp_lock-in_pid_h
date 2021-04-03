# This makefile was made to be executed inside redpitaya ARM envirmonet


CC=gcc
RM=rm

CFLAGS+= -g

all: lock osc streaming stream_tcp_osc_cmd

lock:
	$(CC) -o lock lock.c $(CFLAGS) -Wno-overflow

osc:
	$(CC) -o osc osc.c $(CFLAGS) -Wno-overflow

streaming:
	$(CC) -o streaming streaming.c $(CFLAGS)

stream_tcp_osc_cmd:
	$(CC) -o stream_tcp_osc_cmd stream_tcp_osc_cmd.c $(CFLAGS)  -Wno-incompatible-pointer-types


clean:
	-$(RM) -f lock osc stream_tcp_osc_cmd streaming
