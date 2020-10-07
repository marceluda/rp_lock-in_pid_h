#!/usr/bin/python3

from __future__ import print_function

import signal
from time import time
from time import sleep
import mmap
import sys
import struct
#import subprocess
from datetime import datetime

import argparse




# Some config vars
Dtime  = 2e-3  # seg
Dtime2 = Dtime/2

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


from hugo import osc,li


# Function to handle nice close with CTRL+C
class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self,signum, frame):
        self.kill_now = True


parser = argparse.ArgumentParser()

parser.add_argument("-f", "--file", type=str, default="default",
                    help="filename")
parser.add_argument("-t", "--timeout", type=int, dest='timeout', default=0,
                    help="timeout value. 0 means infinite.")
                    
parser.add_argument('--cnt-store', dest='cnt_store', action='store_true')
parser.add_argument('--no-cnt-store', dest='cnt_store', action='store_false')
parser.set_defaults(cnt_store=True)

parser.add_argument('--params', nargs='+')

args = parser.parse_args()

# nc_cmd = ['nc '+args.server+' '+args.port]


if __name__ == '__main__':
    # Function for nice kill
    killer = GracefulKiller()
    
    # Memory sectors to send
    memcodes=[]
    
    if len(sys.argv)<=1:
        eprint("Usage: ... ")
        eprint(" ")
        numkeys=[y.ljust(20) for y in li.names()]
        for i in range(int(len(numkeys)/5+1)):
            print(', '.join(numkeys[i*5:(i+1)*5]))
        eprint("")
        eprint("Run in server:")
        eprint("nc -l -p 6000 | pv -b >  $( date +%Y%m%d_%H%M%S ).bin ")
        eprint("")
        exit()
    
    now        = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename   = args.file+'_'+now
    t0         = time()   # Store start time
    struct_str = '!f'
    C          = []
    
    print('Time register ' + ( 'on' if args.cnt_store else 'off' ) )
    
    params  = args.params.copy()
    
    if args.cnt_store:
        for par in ['cnt_clk2', 'cnt_clk']:
            if par in params:
                params.pop(params.index(par))
        params = ['cnt_clk2', 'cnt_clk'] + params
    for i in params:
        memcodes.append(li[i].addr)
    ilist  = list(range(len(memcodes)))
    signed = []
    for i in params:
        struct_str += 'L' if 'cnt_clk' in i else 'l'
        signed.append( False if 'cnt_clk' in i else True  )
        C.append(0)
    ss = struct.Struct(struct_str)
    
    
    print(params , struct_str, signed )
    # NetCat proccess to send data to server
    # process = subprocess.Popen(nc_cmd, shell=True, stdin=subprocess.PIPE,stdout=subprocess.PIPE,preexec_fn = preexec_function)
    
    # Write first params and data to txt file
    txt=('Columns: '+','.join(params)+'\n'+'timestamp {:>20f}\n'.format(t0))  #.ljust(99)+'\n').encode('ascii')
    
    #process.stdin.write(txt)
    #process.stdin.flush()
    
    
    # Run: /opt/redpitaya/sbin/rw
    with open(filename+'.txt', 'a') as out_file:
        out_file.write( txt )
        with open("/dev/mem", "r+b") as f:
            mm   = mmap.mmap(f.fileno(), 512, offset=0x40600000)
            txt2 =[]
            for i in li:
                addr = i.addr
                A    = int.from_bytes(mm[addr:addr+4], byteorder='little', signed=True)
                txt2.append( '"{:s}": {:f}'.format(i.name,A) )
            #process.stdin.write( (  ('params={'+',\n'.join(txt2) +'\n}\n').ljust(3399)+'\n' ).encode('ascii') )
        out_file.write( 'params={'+',\n'.join(txt2) +'\n}\n' )
        # process.stdin.flush() 
    
    with open(filename+'.bin', 'a+b') as out_file:
        # Open memory
        with open("/dev/mem", "r+b") as f:
            li.start_clk()
            print(t0)
            tl=time()
            if args.timeout <= 0:
                while True:
                    if (time()-tl>Dtime):
                        li.freeze()
                        for i,addr,sig in zip(ilist,memcodes,signed):
                            C[i]=int.from_bytes(mm[addr:addr+4], byteorder='little', signed=sig)
                        #sys.stdout.buffer.write( ss.pack(time()-t0, *C )  )
                        li.unfreeze()
                        try:
                            out_file.write(  ss.pack(time()-t0, *C ) )
                        except:
                            print('ERROR:')
                            print( time()-t0  )
                            print( C )
                            exit(1)
                        #process.stdin.write( ss.pack(time()-t0, *C ) )
                        #process.stdin.flush()
                    sleep(Dtime2)
                    if killer.kill_now:
                        break
            else:
                while True:
                    if (time()-tl>Dtime):
                        li.freeze()
                        for i,addr,sig in zip(ilist,memcodes,signed):
                            C[i]=int.from_bytes(mm[addr:addr+4], byteorder='little', signed=sig)
                        #sys.stdout.buffer.write( ss.pack(time()-t0, *C )  )
                        li.unfreeze()
                        try:
                            out_file.write(  ss.pack(time()-t0, *C ) )
                        except:
                            print('ERROR:')
                            print( time()-t0  )
                            print( C )
                            exit(1)
                            
                        #process.stdin.write( ss.pack(time()-t0, *C ) )
                        #process.stdin.flush()
                    sleep(Dtime2)
                    if (time()-tl>args.timeout):
                        break
                    if killer.kill_now:
                        break            
    # End code
    
    print("Program finished")
    print('')
    print("pack string: '{:s}'".format(struct_str))




######## Reading example

#from numpy import *
#import matplotlib.pyplot as plt
 
#import struct
 
#fn='/home/lolo/tmp/borrar/archivo2.txt'
 
#cs=struct.calcsize('!fhhh')
#dd=[]
#with open(fn,'rb') as f:
    #txt=f.read(100)
    #fc=f.read(cs)
    #while fc:
        #dd.append(struct.unpack('!fhhh',fc))
        #fc=f.read(cs)
 
#dd=array(dd)
 
#t=array(dd)[:,0]  ;  a=array(dd)[:,1]  ;  b=array(dd)[:,2] ; c=array(dd)[:,3]
 
#plt.plot(t,a,t,b,t,c)
