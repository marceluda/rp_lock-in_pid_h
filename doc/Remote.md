# Remote control

How to control `lock_in+pid_harmonic` v2.3.14 from a program, without the web page. The registers are
described in [FPGA.md](FPGA.md); the meaning of each instrument in [App.md](App.md).

- [Options](#options)
- [HTTP API](#http-api)
  - [`/lock`: lock module registers](#lock-lock-module-registers)
  - [`/osc`: oscilloscope registers and memory](#osc-oscilloscope-registers-and-memory)
  - [Other endpoints](#other-endpoints)
  - [Limitations of `/osc` on the 2.0 FPGA](#limitations-of-osc-on-the-20-fpga)
- [Python with `requests` only](#python-with-requests-only)
- [Python with `control_finn.py`](#python-with-control_finnpy)
- [Recipes](#recipes)
  - [Configure the lock-in](#configure-the-lock-in)
  - [Configure a PID](#configure-a-pid)
  - [Close and check a lock](#close-and-check-a-lock)
  - [Read an oscilloscope acquisition](#read-an-oscilloscope-acquisition)
  - [Streaming](#streaming)
- [Running on the board: `c/` and `py/`](#running-on-the-board-c-and-py)
- [SSH version (deprecated)](#ssh-version-deprecated)
- [Coexistence with the web page](#coexistence-with-the-web-page)

## Options

| Way | Where it runs | Status |
|---|---|---|
| **HTTP API** (`/lock`, `/osc`) + Python (`requests`, `control_finn.py`) | any computer on the network | **recommended** |
| `c/lock`, `c/osc`, `py/*.py` | on the Red Pitaya (SSH) | for scripts on the board, e.g. `py/lock_from_registers.py` |
| SSH version (`resources/remote_control/shh_version`, `control_hugo.py`) | computer, through SSH | deprecated, kept for specific cases |

The web page does not need to be open: the App only has to be **loaded** (FPGA image of this App in the
PL). The App is loaded by opening its page once (or by `http://rp-XXXXXX.local/bazaar?start=lock_in+pid_harmonic`).
Do not use the endpoints while another App is loaded: `c/lock` and `c/osc` access the FPGA addresses
directly.

## HTTP API

The endpoints are defined in `lock_in+pid_harmonic/nginx.conf` (Lua blocks, v2.3.10). Base URL:

```
http://rp-XXXXXX.local/lock_in+pid_harmonic/
```

### `/lock`: lock module registers

`GET /lock_in+pid_harmonic/lock?<query>` runs `/opt/redpitaya/www/apps/lock_in+pid_harmonic/c/lock` with the
query as arguments and returns its output as plain text, one line `name:value` per register:

| Query | Command run | Effect |
|---|---|---|
| (none) | `c/lock` | read all the 99 registers |
| `?in1` or `?in1=` | `c/lock in1` | read `in1` |
| `?aux_A=5` | `c/lock aux_A 5` | write 5 to `aux_A` and read it back |
| `?oscA_sw=12&in1&in2` | `c/lock oscA_sw 12 in1 in2` | several reads and writes (order not guaranteed) |

Rules (from `nginx.conf` and `c/lock.c`):

- Only names matching `[A-Za-z0-9_]+` and **integer** values (`-?[0-9]+`) are passed to the shell; other
  arguments are silently dropped (e.g. `?aux_A=0.5` does nothing). Since v2.3.10 a name without `=` reads.
- The arguments come from a Lua table, so **the order of several arguments in one request is not
  guaranteed**. When the order matters (e.g. the two writes of a lock request) use one request per write.
- Values are decimal. Signed registers accept negative values (two's complement is done by the FPGA).
  Unsigned 32-bit registers accept 0..4294967295 (e.g. `stream_ip`); a negative value is rejected for
  unsigned registers narrower than 32 bits.
- Errors (answer text, HTTP 200): `ERROR: parameter 'x' not found` (stops at the unknown name),
  `ERROR: <name> is read-only and cannot be written`,
  `ERROR: <name> is not a signed register and you tried to sed value -1`.
- `c/lock` prints signed registers as `int32` and unsigned ones as `uint32`.

Example:

```bash
curl "http://rp-XXXXXX.local/lock_in+pid_harmonic/lock?lock_status&lock_control"
# lock_status:4362
# lock_control:1362
```

The register list (name, index, signed, read-only, min, max) is served at
`/lock_in+pid_harmonic/c/lock.txt`.

### `/osc`: oscilloscope registers and memory

`GET /lock_in+pid_harmonic/osc?<query>` runs `c/osc` the same way, on the 20 registers of the scope listed
in `/lock_in+pid_harmonic/c/osc.txt` (`conf`, `TrgSrc`, `ChAth`, `ChBth`, `TrgDelay`, `Dec`, `CurWpt`,
`TrgWpt`, `ChAHys`, `ChBHys`, `AvgEn`, `PreTrgCnt`, `ChAEqFil1..4`, `ChBEqFil1..4`).

- `?Dec&conf=2`: read `Dec`, write 2 to `conf` (reset of the write state machine).
- `?dump`: 16384 lines `:<chA>:<chB>` with the content of both sample buffers (14-bit signed, in buffer
  order, not rotated), followed by the 20 registers `name:value`. The trace starts after the write pointer:
  rotate with `CurWpt` and place t = 0 with `TrgWpt` (see `control_finn.py` `Osc.curv()`).

### Other endpoints

| Endpoint | Answer |
|---|---|
| `/lock_in+pid_harmonic/calib` | output of `/opt/redpitaya/bin/calib -rv` (calibration constants, `NAME = value` lines) |
| `/lock_in+pid_harmonic/get_ip` | IP of the client |
| `/lock_in+pid_harmonic/streaming` | starts `c/streaming` (see [Streaming](#streaming)); answers `OK` |
| `/lock_in+pid_harmonic/check_streaming` | `0` if `c/streaming` is running, `1` if not |
| `/lock_in+pid_harmonic/restart_server` | restarts the nginx of the board |

### Limitations of `/osc` on the 2.0 FPGA

The scope of the 2.0 FPGA **locks its trigger after every trigger** and ignores new triggers until 1 is
written to offset `0x94` (`src/fpga.h` `trigger_lock_ctr`, `rp_scope_cfg.v` l. 227). The C controller of
the web page does it before each acquisition, but `c/osc` only knows the 20 registers up to `0x4C`, so
**an acquisition armed through `/osc` may never trigger** if the last trigger was not followed by an unlock
(e.g. after the web page stopped in Single). Also, `TrgSrc` reads the lock in bit 5, so a loop that waits for
`TrgSrc == 0` (as `control_finn.py` `measure(wait=True)` and `wait_osc_finish()` do) can wait forever.

This has not been tested on the board with v2.3.14: **a confirmar** (request for testAgent). Adding the
unlock register to `c/osc` / `osc.txt` and to `control_finn.py` is a request for devAgent. Meanwhile the
safest way to get a trace is to let the web page acquire it, or to read the buffers with `?dump` after an
acquisition made by the page.

## Python with `requests` only

A minimal client, enough for most scripts:

```python
import requests

URL = 'http://rp-XXXXXX.local/lock_in+pid_harmonic'

def lock_get(*names):
    """Read lock registers; returns a dict name -> int."""
    r = requests.get(f'{URL}/lock', params={n: '' for n in names}, timeout=5)
    r.raise_for_status()
    if 'ERROR' in r.text:
        raise ValueError(r.text)
    return {k: int(v) for k, v in (l.split(':') for l in r.text.strip().split('\n'))}

def lock_set(name, value):
    """Write one lock register (integer) and return the value read back."""
    r = requests.get(f'{URL}/lock', params={name: int(value)}, timeout=5)
    r.raise_for_status()
    if 'ERROR' in r.text:
        raise ValueError(r.text)
    return int(r.text.strip().split(':')[1])

print(lock_get('in1', 'in2', 'lock_status'))
lock_set('aux_A', 820)          # 820 counts = 100 mV
```

## Python with `control_finn.py`

`resources/remote_control/http_version/control_finn.py` (needs `requests`, `numpy`, and `matplotlib` for
plots) wraps the API; `example_usage.py` in the same folder shows its use.

```python
from control_finn import RedPitayaApp, reg_labels

rp = RedPitayaApp('http://rp-XXXXXX.local/lock_in+pid_harmonic/?type=run')   # URL copied from the browser

rp.lock.aux_A                     # read one register
rp.lock.aux_A = 5                 # write one register
rp.lock.oscA_sw = 'cos_ref'       # selectors accept the labels of the UI (reg_labels)
rp.lock.get()                     # dict with all the lock registers
rp.lock.get('in1 in2 error')      # several registers
rp.lock.set({'aux_A': 0, 'aux_B': 0})
rp.osc.get()                      # all the scope registers
```

| Method | What it does |
|---|---|
| `rp.lock.<reg>`, `.get()`, `.set()` | read / write lock registers (names from `c/lock.txt`) |
| `rp.osc.<reg>`, `.get()`, `.set()` | the same for the scope registers |
| `rp.osc.measure(trig, dec, trig_pos, threshold, hysteresis, average, wait)` | prepare and arm an acquisition (`trig`: `'manual'`, `'A_rising'`, `'A_falling'`, `'B_rising'`, `'B_falling'`, `'ext_rising'`, `'ext_falling'`) — see the [limitation](#limitations-of-osc-on-the-20-fpga) |
| `rp.osc.dump()`, `rp.osc.curv(raw=True)` | read the buffers; `curv` returns `t, ch1, ch2` ordered and with t = 0 at the trigger |
| `rp.wait_osc_finish()`, `rp.plot_meas()` | wait for the acquisition, quick plot |
| `rp.save_params()`, `rp.save_last_meas()`, `RedPitayaApp('<file>.npy')` | save registers (and the last trace) to `.npy` and reload them |
| `rp.get_freq()`, `rp.set_freq(hp)`, `rp.set_phase(val)` | modulation frequency (`gen_mod_hp`) and phase (0..2519) |
| `rp.set_modulation_amplitud(val, ch='out1')` | `mod_out1`/`mod_out2` (−1 off .. 8191) |
| `rp.set_lpf(tau_exponent, order, line)`, `rp.get_lpf()` | low-pass filters (τ = 8 ns·2^tau_exponent, 14..29) |
| `rp.get_XY(units='V', F=False)` | X, Y (and F1..F3) from the 28-bit registers, read at the same instant (`read_ctrl[0]`) |
| `rp.streaming_prepare()`, `.streaming_start()`, `.streaming_stop()` | streaming |

Known problems of `control_finn.py` / `example_usage.py` (reported to devAgent, **not tested on 2.0**):

- `measure()` / `wait_osc_finish()` and the 2.0 trigger lock (above).
- `curv(raw=False)` uses `np.float` (removed in NumPy ≥ 1.24) and converts with `FE_CH1_FS_G_HI` /
  `FE_CH1_DC_offs` of `calib -rv`; whether Ecosystem 2.0 prints those names is **a confirmar**. The
  conversion is only meaningful when the channel shows `in1`/`in2`; internal signals are 8192 counts = 1 V.
- `plot_meas()` uses `grid(b=True)` (removed in recent Matplotlib).
- `set_lpf(line='all')` sets only F0..F2 (not F3), and its message prints a fixed τ; `get_lpf()` masks
  `tau` with `& 31` instead of `& 15`.
- `reg_labels`: ISR option 4 is "6 us" (it is 65.5 µs) and `lock_trig_sw` 6-8 have code text as labels.
- `example_usage.py` uses `os` without importing it (section "Load configuration from a web saved json").

## Recipes

Values in counts: 8192 counts = 1 V. The examples use the helpers `lock_get` / `lock_set` above;
the same names work with `rp.lock.<name>`.

### Configure the lock-in

```python
lock_set('signal_sw', 0)         # lock-in input = in1
lock_set('gen_mod_hp', 0)        # modulation 125e6/2520 = 49.6 kHz
lock_set('gen_mod_phase', 0)     # phase of cos_1f..3f (2520 = 360 deg)
lock_set('mod_out1', 100)        # add cos_ref with amplitude ~50 counts (~6 mV) to OUT1 (-1 = off)
lock_set('lpf_F0', (2 << 4) | 1) # X,Y: order 2, tau = 8 ns * 2**15 = 262 us
lock_set('sg_amp0', 5)           # Xo, Yo gain x32
lock_set('error_sw', 2)          # error = Yo
lock_set('error_offset', 0)
```

Read X and Y at the same instant:

```python
lock_set('read_ctrl', 1)                      # freeze the copies
r = lock_get('X_28', 'Y_28')
lock_set('read_ctrl', 0)
X, Y = r['X_28'] / 2**11 / 8192, r['Y_28'] / 2**11 / 8192    # volts, amplitude of each component
```

### Configure a PID

```python
lock_set('pidA_sw', 0)       # input = error
lock_set('pidA_sp', 0)       # set point
lock_set('pidA_PSR', 3)      # kp / 1024
lock_set('pidA_kp', -500)    # -0.488
lock_set('pidA_ISR', 8)      # 2**26 * 8 ns = 537 ms
lock_set('pidA_ki', -20)     # tau_i = 537 ms / 20 = 26.8 ms
lock_set('pidA_kd', 0)
lock_set('pidA_SAT', 13)     # integral term limited to +-1 V
lock_set('pidA_ctrl', 0)     # no reset / freeze
lock_set('out1_sw', 12)      # OUT1 = ctrl_A = PID A + ramp A
```

### Close and check a lock

The lock control is commanded only with `lock_control` and observed in `lock_status`
([`lock_control.md`](../lock_in+pid_harmonic/doc/lock_control.md) §5). Same sequence as
`py/lock_from_registers.py`, over HTTP:

```python
import time

def lock_control_value(now=0, launch=0, manual=('ramp',), final=('pidA',), trig_type=1, rise=1):
    bit = {'pidB': 0, 'pidA': 1, 'ramp': 2}
    v = (now & 1) | (launch & 1) << 1
    v |= sum(1 << (2 + bit[x]) for x in manual)     # enables while not locked
    v |= sum(1 << (5 + bit[x]) for x in final)      # enables while locked
    return v | (trig_type & 3) << 8 | (rise & 1) << 10

def status():
    s = lock_get('lock_status')['lock_status']
    return {'armed': s & 1, 'locked': s >> 1 & 1, 'ramp': s >> 4 & 1,
            'pidA': s >> 3 & 1, 'pidB': s >> 2 & 1, 'count': s >> 8 & 0xff}

# 1) trigger: 16.58 ms after the scan floor (ticks of 8 ns)
lock_set('lock_trig_time', round(16.58e-3 / 8e-9))      # 2072500
# (level trigger instead: lock_trig_sw = 0 (error), lock_trig_val = 5085, trig_type = 2)

# 2) configuration without request (also releases a previous lock), then the request (0->1 edge)
base = lock_control_value(trig_type=1)                  # 0x550 = 1360
lock_set('lock_control', base)
lock_set('lock_control', base | 2)                      # arm (Trigger Lock); base | 1 = Lock Now

# 3) wait for LOCKED
t0 = time.time()
while not status()['locked'] and time.time() - t0 < 10:
    time.sleep(0.01)
print(status())                      # e.g. {'armed': 0, 'locked': 1, 'ramp': 0, 'pidA': 1, ...}

# 4) check: error mean and std over ~1 s
r = lock_get('error_mean', 'error_std')
mean = r['error_mean'] / 2**18
std  = max(r['error_std'] / 32 - mean**2, 0) ** 0.5   # counts (8192 = 1 V)

# 5) release: back to the manual enables (scan running)
lock_set('lock_control', base)
```

Notes:

- A lock request needs a **0→1 edge** of bit 0 or 1: write the value without the request first. Writing
  the same value again does nothing (so the C controller rewriting registers does not disturb a lock).
- The ramp runs only if `ramp_enable` (0x0B0) is also 1.
- Changing a manual enable (bits 4:2) while LOCKED releases the lock.
- On the board, `python3 py/lock_from_registers.py --trig time --time 16.58ms --set pidA` does the same
  (with `--status`, `--release`, `--now`, `--force`); tested on the board, locked in 0.062 s
  (`reportes/lock-in_pid_h_lock_test/2026-10-08_22:45:40_lock.md` §2.5).

### Read an oscilloscope acquisition

With the limitation above in mind, the buffers can always be read after an acquisition made by the web
page (e.g. a Single, or a lock capture):

```python
import numpy as np

r = requests.get(f'{URL}/osc', params={'dump': ''}, timeout=10).text.strip().split('\n')
cha = np.array([int(l.split(':')[1]) for l in r if l.count(':') == 2])
chb = np.array([int(l.split(':')[2]) for l in r if l.count(':') == 2])
reg = {l.split(':')[0]: int(l.split(':')[1]) for l in r if l.count(':') == 1}

cur, trg = (reg['CurWpt'] + 1) % 16384, reg['TrgWpt']
cha, chb = np.roll(cha, -cur), np.roll(chb, -cur)       # oldest sample first
t = (np.arange(16384) - (trg - cur) % 16384) * 8e-9 * reg['Dec']   # t = 0 at the trigger
# cha, chb in counts of the signals chosen by oscA_sw / oscB_sw (8192 = 1 V)
```

### Streaming

```python
def ip_to_reg(ip):                         # 'a.b.c.d' -> a + b<<8 + c<<16 + d<<24
    return sum(int(v) << (8 * i) for i, v in enumerate(ip.split('.')))

lock_set('oscA_sw', 1); lock_set('oscB_sw', 3)   # channels to stream: in1, error
lock_set('stream_ip', ip_to_reg('192.168.1.10'))
lock_set('stream_port', 6000)
lock_set('stream_rate', 128)                     # decimation 128: 0.98 MS/s
requests.get(f'{URL}/streaming')                 # start c/streaming on the board
lock_set('stream_cmd', 1)                        # start sending (a receiver must be listening)
# ...
lock_set('stream_cmd', 0)                        # stop
```

The receiver (`resources/streaming/server`, or `nc -l <port> > file.bin`) and the format of the data are
described in `resources/README.md` (`resources/streaming/read_bin.py` reads the file).

## Running on the board: `c/` and `py/`

On the board (`ssh root@rp-XXXXXX.local`), in `/opt/redpitaya/www/apps/lock_in+pid_harmonic/`:

```bash
c/lock                      # all lock registers
c/lock in1 in2 out1 out2    # read some
c/lock oscA_sw 12 in1       # write and read
c/osc                       # scope registers
c/osc dump                  # buffers + registers
python3 py/lock_from_registers.py --status
```

`py/hugo.py` is a Python module with the same register tables (mmap of `/dev/mem`) used by the other
scripts: `lock.py`/`osc.py` (read/write like `c/lock`/`c/osc`), `lock_reg_table.py` (print the table),
`osc_get_ch.py` (read the channels), `osc_trig.py` (triggered acquisition), `data_dump.py` and
`data_dump_file.py` (long acquisitions to a TCP server or to a file), and `lock_from_registers.py`.
Running them creates `py/__pycache__/` on the board (harmless). The scripts other than
`lock_from_registers.py` have not been re-tested on the 2.0 version (**a confirmar**; `osc_trig.py` has the
same trigger-unlock limitation as `c/osc`).

## SSH version (deprecated)

`resources/remote_control/shh_version/` (`control_hugo.py`, `example.py`, `example_streaming.py`,
`config_RP.py`, …) controls the App by running the `py/` scripts on the board through SSH. It predates the
HTTP API and is kept only for specific cases (e.g. long acquisitions written on the board). v2.3.13 fixed
`launch_lock()`/`lock_now()` and added `release_lock()`/`lock_status()` in `control_hugo.py`. New scripts
should use the HTTP API.

## Coexistence with the web page

- The web page and a script can be used at the same time: the page reads the registers on every request
  and shows changes made from outside (e.g. a lock closed from Python), without sending anything back.
- The C controller writes `lock_control` only when the user changes a lock button or checkbox. **The other
  lock registers are rewritten with the controller's copy when the user changes any lock parameter in the
  page**, so a value written from a script can be overwritten by a later change in the page
  (`py/lock_from_registers.py` docstring).
- Do not acquire with `/osc` while the page is acquiring: stop the page with a Single acquisition first
  (both use the same scope).
- Opening the page in a new tab restores that tab's state and sends the transient commands
  (`lock_ctrl_aux_lock_now`, `lock_ctrl_aux_launch_lock_trig`, `lock_stream_cmd`) as 0
  (`index.html` `state_transient_zero`), which **probably releases an active lock** (a confirmar).
