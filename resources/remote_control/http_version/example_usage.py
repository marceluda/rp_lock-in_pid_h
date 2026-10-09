#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of remote control by control Finn

Each "#%%" block is a cell (Spyder / VS Code / IPython): run them one by one.
Tested with the App v2.3.15 on Ecosystem 2.0 (RedPitaya_OS 2.04); scope_stop()/scope_auto(): v2.3.16.
"""

import os
import json

from time import sleep

from control_finn import RedPitayaApp, reg_labels


#%%  Connect to RP

# URL of the App (as copied from the browser; '?type=run' is removed)
URL = os.environ.get('RP_URL', 'http://rp-XXXXXX.local/lock_in+pid_harmonic/?type=run')

rp =  RedPitayaApp(URL)

print(rp)
print('Calibration constants read:', len(rp.calib))



#%% Example configuration and acquisition #####################################

"""
The C controller of the App (the scope of the web page) keeps acquiring in Auto after the App is
started, even with no web page open, and uses the same scope. osc.measure() / acquire() stop it first
(trig_mode = 2, as a Single acquisition of the page): rp.scope_stop(). Give the scope back to the page
with rp.scope_auto() (see the cell "Give the scope back to the web page" below).
If it can not be confirmed stopped (no answer of POST /data), acquire() raises
control_finn.WebScopeNotStopped and does not acquire: try again, or press Single in the web page.
"""

print('scope of the web page, trig_mode (0 Auto, 1 Normal, 2 Single):', rp.scope_mode())

rp.lock.oscA_sw = 'cos_ref'
rp.lock.oscB_sw = 'sin_ref'

rp.lock.gen_mod_hp = 255

# trigger on the rising edge of channel A (cos_ref) at 0, 20 samples before the trigger
rp.osc.measure('A_rising', dec=256 , trig_pos=20 , threshold=0, wait=True)

rp.wait_osc_finish()   # (already finished: wait=True above)

tt, ch1, ch2 = rp.osc.curv()

rp.plot_meas()




#%% get the data  #############################################################


rp.lock.oscA_sw = 'cos_ref'
rp.lock.oscB_sw = 'sin_ref'

rp.lock.gen_mod_hp = 255

# measure + wait + curv in one call. raw=False: Volts
tt, ch1, ch2 = rp.acquire('A_rising', dec=256 , trig_pos=20, raw=False)


from matplotlib import pyplot as plt

plt.figure()
plt.plot(tt,ch1,tt,ch2)


#%% Manual trigger and external (lock module) trigger  #########################

# manual: triggers at once, trigger in the middle of the trace
tt, ch1, ch2 = rp.acquire('manual', dec=64, trig_pos=0.5)

# external: the trigger made by the lock module (lock.trig_sw), e.g. the scan floor of the ramp
rp.lock.trig_sw = 'Scan floor'
tt, ch1, ch2 = rp.acquire('ext_rising', dec=1024, trig_pos=0.1, timeout=20)


#%% Give the scope back to the web page  ######################################

# The acquisitions above stopped the scope of the web page (C controller): restart it in Auto.
rp.scope_auto()
print('trig_mode:', rp.scope_mode())

# To acquire from Python while the web page keeps its scope running (not recommended: the data
# can be mixed), disable the automatic stop:
#   rp.osc.auto_stop_web_scope = False      or      rp.acquire(..., stop_web_scope=False)


#%% save data and load it later  ##############################################



rp.lock.oscA_sw = 'cos_ref'
rp.lock.oscB_sw = 'sin_ref'

rp.lock.gen_mod_hp = 255

rp.osc.measure('A_rising', dec=256 , trig_pos=20 , wait=True)

rp.wait_osc_finish()

tt, ch1, ch2 = rp.osc.curv()

fn = rp.save_last_meas()

print(f"You saved data in file: {fn}")



#%% Load saveda data
rp2 =  RedPitayaApp(fn)

# rp2._last_osc_dump is a dict with the saved data


rp2.plot_meas()


tt, ch1, ch2 = rp2.osc.curv('last')
plt.figure()
plt.plot(tt,ch1,tt,ch2)



#%% Lock-in: input, frequency, phase, filters, gains  #########################

rp.set_signal('in1')                 # lock-in input (signal_sw)
print('f =', rp.set_freq_hz(10e3), 'Hz')          # closest modulation frequency (gen_mod_hp)
print('f =', rp.set_freq(255), 'Hz')               # or with the register value
print('phase =', rp.set_phase(630), 'deg')         # cos_1f..3f phase (2520 = 360 deg)
rp.set_modulation_amplitud(-1, ch='out1')          # -1: no modulation added to OUT1

rp.set_lpf(tau_exponent=15, order=2, line='ref')   # X, Y: tau = 8 ns * 2**15 = 262 us, 2nd order
rp.set_lpf(tau_exponent=18, order=1, line='all')   # the four lines
print(rp.get_lpf())                                # dict name -> (tau [s], order)
print(rp.get_lpf('ref'))

rp.set_gain('ref', 'x32')            # Xo, Yo = X, Y * 32
print('X, Y [V] =', rp.get_XY())
print('X, Y, F1, F2, F3 [int] =', rp.get_XY(units='int', F=True))


#%% PID  ######################################################################

rp.set_pid('A', sw='error', sp=0, kp=0, ki=0, kd=0, PSR='/1024', ISR='537 ms', DSR=0, SAT=13)
print(rp.get_pid('A'))
rp.pid_reset('A')                    # integrator reset

rp.lock.error_sw = 'Yo'              # error signal = Yo
rp.lock.out1_sw  = 'ctrl_A'          # OUT1 = PID A + ramp A


#%% Ramp (scan)  ##############################################################

rp.set_ramp(step=100, low=-4000, high=4000, sawtooth=False, enable=True)
rp.set_manual(ramp=True, pidA=False, pidB=False)   # "Scan enable": the ramp runs, PIDs off
print(rp.get_ramp())
print(rp.lock_status())


#%% Lock  #####################################################################

# configuration: time trigger 16.58 ms after the scan floor, PID A on (ramp off) while locked
rp.lock_config(trig='time', time=16.58e-3, final=('pidA',))
st = rp.lock_launch(timeout=10)      # Trigger Lock and wait for LOCKED
print(st)                            # {'armed': False, 'locked': True, 'pidA': True, ...}

rp.lock_release()                    # back to the manual enables (scan)

# level trigger: error crossing 0.1 V upwards
rp.lock_config(trig='level', level_V=0.1, signal='error', rise=True, final=('pidA',))
rp.lock_launch()
rp.wait_locked(timeout=10)
rp.lock_release()

# lock now
rp.lock_now()
print(rp.lock_status())
rp.lock_release()


#%% Get all the registers of Lock module in FPGA ##############################

all_lock_regs = rp.lock.get()



#%% Interpretation of integers registers ######################################

for reg in 'oscA_sw oscB_sw'.split():
    value = rp.lock.get(reg)
    print(f'{reg} = {value}')

for reg in 'oscA_sw oscB_sw'.split():
    value = rp.lock.get(reg)
    label = reg_labels[reg][value]
    print(f'{reg} = "{label}"')







#%% Load configuration from a web saved json ##################################

fn = 'RP.json'


if os.path.isfile(fn):
    with open(fn,'r') as rpcur_fp:
        rpcur_config = json.load(rpcur_fp)

    config_lock = { k[5:]:v for k,v in rpcur_config['data'].items() if k[:5]=='lock_' }

    # Load only RW registers
    for key, val in config_lock.items():
        if key in rp.lock._registers.keys() and not rp.lock._registers[key][2]:
            print(key)
            rp.lock.set(key,val)




#%% Streaming example #########################################################

def IPtoReg(txt):
    vec = txt.strip().split('.')
    if not len(vec) == 4:
        raise ValueError('this is not an IPv4')

    return sum([ int(v)<<(i*8) for i,v in enumerate(vec) ])

def REgtoIP(val):
    return f'{val&255}.{(val>>8)&255}.{(val>>8*2)&255}.{(val>>8*3)&255}'


rp.lock.oscA_sw  = 'sin_ref'
rp.lock.oscB_sw  = 'cos_3f'



rp.lock.stream_rate = 1024

rp.lock.stream_port = 6000

REgtoIP( rp.lock.stream_ip )


rp.streaming_prepare()


rp.streaming_start()

rp.streaming_stop()
