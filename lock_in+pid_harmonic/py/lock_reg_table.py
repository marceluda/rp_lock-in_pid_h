#!/usr/bin/python3
from __future__ import print_function

from time import sleep
import mmap
import sys



def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

from hugo import osc,li

if __name__ == '__main__':    
    # Memory sectors to send
    
    for r in li.regs:
        #print( f'{r.index:3d}, {r.name:20} , {r.addr:04d} , { "ro" if r.ro else "rw" }, {r.nbits:2d }, {r.signed} ')
        print( str(r.index).rjust(3), r.name.ljust(20) , r.addr, hex(li.base_addr+r.addr) ,  "ro" if r.ro else "rw", str(r.nbits).rjust(3), ' int' if r.signed else 'uint')

