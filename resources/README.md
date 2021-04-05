# Resources


This folder has some useful scripts and information for Development and App advances usage.


## Folders content
  * `code_helpers`: This folder has some scripts for automatic generation of verilog code
  * `process_web_download`: Scripts for viewing data downloaded from the Web App
  * `rp_cmds`: Scripts to run inside RedPitaya device shell
  * `streaming`: Streaming oscilloscope channels to a computer
  * `remote_control`: Remote control of the App using programing language


# Streaming Service

The streaming service lets you send the oscilloscope channels data to a computer in a continued stream.

It works by continuously reading the channels buffer and sending the information through TCP protocol to a server that must be listening on a remote computer.

The continuity of the may be broken if the RedPitaya operative system has lots of processor interruptions (if it is on a heavy load work). This affects only thes fastest Sample rate options. In the test made in the lab, using decimation 128 (0.98 MS/sec), some interruptions may appear in the first half second of streaming and then the continuity is kept without problems .

## Instructions for Streaming

  1. Build the local server (NOTE: The code is for Linux OS, but if you port it to windows, please, conctac me to inclue it in this project ).

```bash
cd resources/streaming
make clean
make
```
  You cas also use other program like `netcat`: `nc -l <ip> <port>`
  
  2. (OPTIONAL) Modify RedPitaya streaming programs and build them

```bash
ssh rp-XXXXXX.local -l root
rw
cd /opt/redpitaya/www/apps/lock_in+pid_harmonic/c
# Modify streaming.c and stream_tcp_osc_cmd.c
make clean
make all
```

  3. On the Web App, unroll the Streaming panel
  4. Configure the server IP and port. To load the IP of the computer where you run the browser, just click on the IP button. The port for the included server is 6000
  5. Choose streaming rate. 0.98 MS/sec is the fastest streaming for continuous data, but continuity may be broken for the first half second.
  6. Click "Prepare Streaming"
  7. THIS IS IMPORTANT: Stop the Web App acquisition. To do this, make a Single acquisition of the oscilloscope. The reason: Only the C program must read the channels buffer. If the web App isn't stopped, it will interfere and ruin your streaming data.
  8. Click the "Start" button to start sending data.
  9. When you want to stop, click the "Start" button.


If you want, you can make streaming from the RedPitaya Shell command line. To do this:

  1. Choose the streaming channels (for example, using the Web App)
  2. Choose the streaming rate.
  3. Stop the Web App acquisition.
  4. Login to RedPitaya shell and run the streaming command

```bash
ssh rp-XXXXXX.local -l root
rw
cd /opt/redpitaya/www/apps/lock_in+pid_harmonic/c

./stream_tcp_osc_cmd <server_ip> <server_port> <send_min_len>

```

  The last param, `send_min_len`, controls the min number of Samples sent per message. Can be tuned to avoid continuity interruption. The best value used now is `64`.

 
