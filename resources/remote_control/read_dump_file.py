#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
read file created with:
    /opt/redpitaya/www/apps/lock_in+pid_harmonic/py/data_dump_file.py
"""


from numpy import *
import matplotlib.pyplot as plt

import struct


#%%

filename = 'lolo_20201002_142028'


with open(f'{filename}.txt','r') as fn:
    txt = fn.readline()


if 'Columns' in txt:
    reg_names = txt.strip().split(' ')[1].split(',')
else:
    raise ValueError(f'Columns not in txt file: {filename}.txt')
    



bin_str='!f'

for reg_name in reg_names:
    bin_str +=  'L' if 'cnt_clk' in reg_name else 'l'
    


cs = struct.calcsize(bin_str)


ii = 0

data = []
tt   = []
with open(f'{filename}.bin','rb') as f:
    goon = True
    while goon:
        fc    = f.read(cs)
        if len(fc)==0:
            goon=False
        else:
            tmp   = list(struct.unpack( bin_str ,fc))
            tt   += [ tmp[0]  ]
            data += [ tmp[1:] ]


data = array(data)
tt   = array(tt)


#%% plot line


fig, axx = plt.subplots(2,2, figsize=(14,9) , sharex='col')


# ax.plot(tt, data[:,0] , '.' )
# ax.plot(tt, data[:,1] , '.' )

cnt   =  (data[:,0]<<32) + data[:,1]
cnt_t = cnt * 8e-9


ax = axx[0,0]
ax.plot(tt, cnt , '.' )
ax.set_ylabel('cnt [int]')
#ax.set_xlalbel('t [seg]')



ax = axx[1,0]
ax.plot((cnt-cnt[0])*8e-9, (cnt-cnt[0])*8e-9 - (tt-tt[0])  , '.' )
ax.set_ylabel('( cnt_time - t ) [s]')
ax.set_xlabel('t [s]')


lims = linspace(2.6,3.6,101)
ax = axx[0,1]
ax.hist(diff(tt)*1e3, lims , label='t')
ax.legend()

ax = axx[1,1]
ax.hist(diff(cnt_t)*1e3, lims , label=r'cnt$\cdot$ 8 ns')
ax.set_xlabel(r'$\Delta t$ [ms]')
ax.legend()


for ax in axx.flatten():
    ax.grid(b=True,linestyle='--',color='lightgray')

for ax in axx[:,1].flatten():
    ax.yaxis.set_ticks_position('right')
    ax.yaxis.set_label_position('right')

fig.tight_layout(h_pad=0.1, w_pad=0.1)

#fig.tight_layout()

# ax.plot(data[:,0])


#%% plot hist



fig, ax = plt.subplots(1,1, figsize=(14,9))


for ii in [2,3,4]:
    dat = data[:,ii]
    ax.plot( cnt_t ,dat , alpha =0.8 , label=reg_names[ii] )

ax.legend()




















