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

  1. Build the local server (NOTE: The code is for Linux OS, but if you port it to windows, please, contact me to include it in this project ).

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


The `read_bin.py` script lets you read the created binary file, with the data received by the server .


# Remote control

There are new and better resources for remote control now. The old (and not recommended) system was made on python and can be accessed still on `resources/remote_control/shh_version`.

The new version consist on three parts:
  * Some C programs on RedPitaya shell that lets you change the FPGA registers of the oscilloscope and the Lock module.
  * A web API that lets you access this programs by HTTP GET requests
  * A local client to read and write the FPGA registers through the API. This last part is implemented in Python, but can be implemented in any language.



## Registers access on FPGA

You can use this by logging into the Red Pitaya shell. You can modify them and re-build them:

```bash
ssh rp-XXXXXX.local -l root
rw
cd /opt/redpitaya/www/apps/lock_in+pid_harmonic/c

make clean
make all
```

Then, in that folder, the `osc` commands control and read the Oscilloscope registers, and the `lock` command does the same with lock module registers.

You can run them without arguments to get all the registers names and values:

```bash
./osc
# conf:1
# TrgSrc:0
# ChAth:0
# ChBth:11384
# TrgDelay:11940
# Dec:1024
# CurWpt:7497
# ...
# ChBEqFil3:14260634
# ChBEqFil4:9830
```

```bash
./lock
oscA_sw:17
oscB_sw:0
osc_ctrl:0
trig_sw:0
out1_sw:0
out2_sw:0
...
aux_A:0
aux_B:0
stream_ip:0
stream_port:6000
stream_rate:128
stream_cmd:0
```


Or you can use them to read just a couple of registers

```bash
./lock in1 in2 out1 out2
# in1:-137
# in2:28
# out1:0
# out2:0
```

set the values of registers

```bash
./lock oscA_sw 12
# oscA_sw:12
```


Or both (if you put an integer after a reg name, it will write it ):

```bash
./lock oscA_sw 12 in1 in2
# oscA_sw:12
# in1:-145
# in2:22
```


## Registers access through API

The same commands can be accessed using the virtual URI :

If you access to:
`http://rp-XXXXXX.local/lock_in+pid_harmonic/osc?Dec=&conf=2`

You will read `Dec` register and set and read `conf=2` in the oscilloscope module.

IMPORTANT: GET protocol will only work if you put the `=` character after the reg name for only reading operation.

The same thing can be used for `lock` module. If you don't send params, all the registers are read:

`http://rp-XXXXXX.local/lock_in+pid_harmonic/lock`


You can use this in python using this:

```python
import requests

res = requests.get('http://rp-XXXXXX.local/lock_in+pid_harmonic/osc', {'Dec'̈́:'' , 'conf': 2 } )
if res.ok:
    print(res.text)
else:
    print('ERROR')
```

Also, you can access registers information through this files:

  * `http://rp-XXXXXX.local/lock_in+pid_harmonic/c/osc.txt`
  *  `http://rp-XXXXXX.local/lock_in+pid_harmonic/c/lock.txt`


## Python programs to access the API


```python

# Load rp APP
from control_finn import RedPitayaApp
rp = RedPitayaApp('http://rp-f00a3b.local/lock_in+pid_harmonic/?type=run')


# Configure acquisition

rp.osc.measure('A_ri', dec=128 , trig_pos=8191 , hysteresis=1, threshold=0, wait=True)

# Get the data
tt , ch1 , ch2 = rp.osc.curv(raw=False)

# plot it
from matplotlib import pyplot as plt
plt.figure()
plt.plot(tt,ch1,tt,ch2)


# Read all the registers of Oscilloscope module
rp.osc.get()
Out[6]:
{'conf': 0,
 'TrgSrc': 0,
 'ChAth': 0,
 'ChBth': 5000,
 'TrgDelay': 8193,
 'Dec': 128,
 'CurWpt': 1645,
 'TrgWpt': 9836,
 'ChAHys': 1,
 'ChBHys': 1,
 'AvgEn': 0,
 'PreTrgCnt': 239213,
 'ChAEqFil1': 32147,
 'ChAEqFil2': 276423,
 'ChAEqFil3': 14260634,
 'ChAEqFil4': 9830,
 'ChBEqFil1': 32147,
 'ChBEqFil2': 276423,
 'ChBEqFil3': 14260634,
 'ChBEqFil4': 9830}

# Read ONE register from lock module:
print( rp.lock.aux_A )

# Set ONE register of lock module:
rp.lock.aux_A= 5

```

NOTE: To make oscilloscope acquisition, first stop the acquisition on the Web App by a single acquisition measurement.
