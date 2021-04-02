# -*- coding: utf-8 -*-

# You need paramiko for Red Pitaya conecction

# If you use Anaconda, run from console:
# conda install -c anaconda paramiko

#%%

from numpy import *
import numpy as np
from matplotlib import pyplot as plt
from time import sleep,time


# PATH of control_hugo.py file
import sys

from control_hugo import red_pitaya_control,red_pitaya_app

AppName      = 'lock_in+pid_harmonic'
host         = 'rp-f00a3b.local'
port         = 22  # default port
trigger_type = 6   # 6 is externa trigger




#%%



filename = 'test.npz'
rp=red_pitaya_app(AppName=AppName,host=host,port=port,filename=filename,password='root')

# reduce log noise on Windows platform
import logging
logging.basicConfig()
logging.getLogger("paramiko").setLevel(logging.WARNING)
rp.verbose = False

#%%


rp.start_streaming(signals='oscA oscB',log='Arrancamos')

sleep(1000)

rp.stop_streaming()



#%%
from read_dump import read_dump,struct

d = read_dump('20201221_102244_dump.bin')


d.load_params()
d.time_stats()


d.load_time()


d.plot('oscA,oscB'.split(','))



d.allan_range2('oscA' ,start=0,end=42800)
d.plot_allan_error(0)



d.allan_range2('oscB' ,start=0,end=42800)
d.plot_allan_error(1)



