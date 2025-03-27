#!/usr/bin/python
#Script for generating fpga/rtl/lock/data_cos_ss.dat 
import numpy as np

#best guess at original distribution
#n = 630
#datacos = [2*int(((1<<11)-0.5)*np.cos(0.5*np.pi*(i+0.5)/n)+0.5) for i in range(n+1)]

#modified distribution
n = 1250
datacos = [int(((1<<13)-1)*np.cos(0.5*np.pi*i/n)+0.5) for i in range(n+1)]

for i in range(len(datacos)):
    print("{:014b}".format(datacos[i]))
