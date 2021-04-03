CC=gcc
RM=rm

CFLAGS+= -g


all: server

server:
	$(CC) -o server server.c $(CFLAGS)   -Wno-incompatible-pointer-types

clean:
	-$(RM) -f server
