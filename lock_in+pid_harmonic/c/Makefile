# This makefile was made to be executed inside redpitaya ARM envirmonet


CC=gcc
RM=rm

CFLAGS+= -g

all: lock osc

lock:
	$(CC) -o lock lock.c $(CFLAGS) -Wno-overflow

osc:
	$(CC) -o osc osc.c $(CFLAGS) -Wno-overflow


clean:
	-$(RM) -f lock osc
