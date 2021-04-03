#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
read bunary file created with streaming server
"""


import numpy as np
import matplotlib.pyplot as plt

import struct

from time import time
from glob import glob

#%% Load last file and plot it

# Load last file in folder
filename = sorted(glob('*.bin'))[-1]

# This is forl building the time array
DELTA_T = 8e-9 * 128   # seconds



bin_str = '<hh'     # two int16 data type
cs      = struct.calcsize(bin_str)

t0      = time()    # this is for measuring elapsed time on large data


ii    = 0

oscA  = []
oscB  = []
tt    = []


with open(f'{filename}','rb') as f:
    goon = True

    while goon:
        fc    = f.read(cs)
        if len(fc)<2  : # or fc.decode()=='\n':
            goon=False
        else:
            tmp   = list(struct.unpack( bin_str ,fc))
            
            tt.append(ii)
            oscA.append( tmp[0] )
            oscB.append( tmp[1] )
            
            ii += 1
            
            # Stop on first millon, just to see 
            if ii>1e6:
                goon=False


tf = time()-t0
print(f'\n\n\nLoad Time: {tf} seg | {round(tf/60,1)} min')




# Convert to numpy array

oscA  = np.array(oscA)
oscB  = np.array(oscB)
tt    = np.array(tt)   * DELTA_T


# Plot channels
fig, ax = plt.subplots( 2,1 , figsize=(13,7) ,  constrained_layout=True , sharex=True)

ax[0].plot(  tt   ,   oscA    ,'-', ms=3 )
ax[1].plot(  tt   ,   oscB    ,'-', ms=3)

ax[0].set_ylabel('oscA')
ax[1].set_ylabel('oscB')

ax[1].set_xlabel('time [sec]')



#%%


