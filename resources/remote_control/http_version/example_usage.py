#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of remote control by control Finn
"""


from control_finn import RedPitayaApp, reg_labels


#%%  Connect to RP



rp =  RedPitayaApp('http://rp-XXXXXX.local/lock_in+pid_harmonic/?type=run')






#%% Example configuration and acauisition #####################################

"""
WARNING:
    befor any acquisition you should stop the Web oscilloscope by
    making a single acquisition.
"""

rp.lock.oscA_sw = 'cos_ref'
rp.lock.oscB_sw = 'sin_ref'

rp.lock.gen_mod_hp = 255

rp.osc.measure('A_rising', dec=256 , trig_pos=20 , wait=True)

rp.wait_osc_finish()

tt, ch1, ch2 = rp.osc.curv()

rp.plot_meas()




#%% get the data  #############################################################


rp.lock.oscA_sw = 'cos_ref'
rp.lock.oscB_sw = 'sin_ref'

rp.lock.gen_mod_hp = 255

rp.osc.measure('A_rising', dec=256 , trig_pos=20 , wait=True)

rp.wait_osc_finish()

tt, ch1, ch2 = rp.osc.curv()


from matplotlib import pyplot as plt


plt.plot(tt,ch1,tt,ch2)


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


tt, ch1, ch2 = rp.osc.curv('last')
plt.figure()
plt.plot(tt,ch1,tt,ch2)



#%% Get all the registers of Lock module in FPGA ##############################

all_lock_regs = rp.lock.get()



#%% Interpretation of integers registers ######################################

from control_finn import reg_labels


for reg in 'oscA_sw oscB_sw'.split():
    value = rp.lock.get(reg)
    print(f'{reg} = {value}')

for reg in 'oscA_sw oscB_sw'.split():
    value = rp.lock.get(reg)
    label = reg_labels[reg][value]
    print(f'{reg} = "{label}"')







#%% Load configuration from a web saved json ##################################

import json

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
