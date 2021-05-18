#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Library for remote control of Lock-in+PID App on RedPitaya
"""



#%%



import requests
import numpy as np
from time import sleep,time


from datetime import datetime


import os



#%% Class for lock module

reg_labels = {
    'oscA_sw': {0: '0',   1: 'in1',   2: 'in2',   3: 'error',   4: 'ctrl_A',   5: 'ctrl_B',   6: 'Ramp A',   7: 'Ramp B',   8: 'pidA_in',   9: 'pidB_in',   10: 'PID A out',   11: 'PID B out',   12: 'sin_ref',   13: 'cos_ref',   14: 'cos_1f',   15: 'cos_2f',   16: 'cos_3f',   17: 'Xo',   18: 'Yo',   19: 'F1o',   20: 'F2o',   21: 'F3o',   22: 'signal_i',   23: 'out1',   24: 'out2'},
    'oscB_sw': {0: '0',   1: 'in1',   2: 'in2',   3: 'error',   4: 'ctrl_A',   5: 'ctrl_B',   6: 'Ramp A',   7: 'Ramp B',   8: 'pidA_in',   9: 'pidB_in',   10: 'PID A out',   11: 'PID B out',   12: 'sin_ref',   13: 'cos_ref',   14: 'cos_1f',   15: 'cos_2f',   16: 'cos_3f',   17: 'Xo',   18: 'Yo',   19: 'F1o',   20: 'F2o',   21: 'F3o',   22: 'signal_i',   23: 'out1',   24: 'out2'},
    'trig_sw': {0: 'None',   1: 'Pin',   2: 'Scan floor',   4: 'Scan ceil',   8: 'harmonic mod.',   16: 'Square mod.',   32: 'Out of lock',   64: 'Jump trigger',   128: 'Lock control trig'},
    'out1_sw': {0: '0',   1: 'in1',   2: 'in2',   3: 'in1-in2',   4: 'error',   5: 'cos_1f',   6: 'cos_2f',   7: 'cos_3f',   8: 'cos_ref',   9: 'sin_ref',   10: 'PID A out',   11: 'PID B out',   12: 'ctrl_A',   13: 'ctrl_B',   14: 'aux_A',   15: 'aux_B'},
    'out2_sw': {0: '0',   1: 'in1',   2: 'in2',   3: 'in1-in2',   4: 'error',   5: 'cos_1f',   6: 'cos_2f',   7: 'cos_3f',   8: 'cos_ref',   9: 'sin_ref',   10: 'PID A out',   11: 'PID B out',   12: 'ctrl_A',   13: 'ctrl_B',   14: 'aux_A',   15: 'aux_B'},
    'lock_trig_sw': {0: 'error',   1: 'Xo',   2: 'Yo',   3: 'F1o',   4: 'F2o',   5: 'F3o',   6: "/*sqXo */ 14'b0",   7: "/*sqYo */ 14'b0",   8: "/*sqFo */ 14'b0",   9: 'signal_i',   10: 'Ramp A',   11: 'aux_A',   12: 'in1',   13: 'in2',   14: 'in1-in2',   15: 'PID A out'},
    'rl_signal_sw': {0: 'in1',   1: 'in2',   2: 'in1-in2',   3: 'aux_A',   4: 'aux_B',   5: '0',   6: '0',   7: '0'},
    'signal_sw': {0: 'in1',   1: 'in2',   2: 'in1-in2',   3: 'cos_ref',   4: 'sin_ref',   5: 'cos_1f',   6: 'aux_A',   7: 'Ramp A'},
    'sg_amp0': {0: 'x1',   1: 'x2',   2: 'x4',   3: 'x8',   4: 'x16',   5: 'x32',   6: 'x64',   7: 'x128',   8: 'x256',   9: 'x512',   10: 'x1k',   11: 'x2k',   12: 'x4k',   13: 'x8k',   14: 'x16k',   15: 'x32k',   16: 'x64k',   17: 'x128k',   18: 'x256k',   19: 'x512k'},
    'sg_amp1': {0: 'x1',   1: 'x2',   2: 'x4',   3: 'x8',   4: 'x16',   5: 'x32',   6: 'x64',   7: 'x128',   8: 'x256',   9: 'x512'},
    'sg_amp2': {0: 'x1',   1: 'x2',   2: 'x4',   3: 'x8',   4: 'x16',   5: 'x32',   6: 'x64',   7: 'x128',   8: 'x256',   9: 'x512'},
    'sg_amp3': {0: 'x1',   1: 'x2',   2: 'x4',   3: 'x8',   4: 'x16',   5: 'x32',   6: 'x64',   7: 'x128',   8: 'x256',   9: 'x512'},
    'error_sw': {0: '0',   1: 'Xo',   2: 'Yo',   3: 'F1o',   4: 'F2o',   5: 'F3o',   6: 'in1',   7: 'in1-in2'},
    'pidA_sw': {0: 'error',   1: 'Xo',   2: 'Yo',   3: 'F1o',   4: 'F2o',   5: 'F3o',   6: 'signal_i',   7: 'Ramp A',   8: 'in1-in2',   9: 'in1',   10: 'in2',   11: 'aux_A',   12: 'aux_B',   13: 'cos_ref',   14: 'sin_ref',   15: '0'},
    'pidA_PSR': {0: '/1', 1: '/8', 2: '/64', 3: '/1024', 4: '/4096'},
    'pidA_ISR': {0: '8 ns',   1: '64 ns',   2: '512 ns',   3: '8 us',   4: '6 us',   5: '524 us',   6: '8 ms',   7: '67 ms',   8: '537 ms',   9: '9 s'},
    'pidA_DSR': {0: '7.5 ns',   1: '60 ns',   2: '480 ns',   3: '7.68 us',   4: '61.44 us',   5: '491.5 us'},
    'pidA_SAT': {0: '±122uV',   1: '±244uV',   2: '±488uV',   3: '±977uV',   4: '±2mV',   5: '±4mV',   6: '±8mV',   7: '±16mV',   8: '±31mV',   9: '±62mV',   10: '±125mV',   11: '±250mV',   12: '±500mV',   13: '±1 V'},
    'pidB_sw': {0: 'error',   1: 'Xo',   2: 'Yo',   3: 'F1o',   4: 'F2o',   5: 'F3o',   6: 'signal_i',   7: 'Ramp A',   8: 'in1-in2',   9: 'in1',   10: 'in2',   11: 'aux_A',   12: 'aux_B',   13: 'cos_ref',   14: 'sin_ref',   15: '0'},
    'pidB_PSR': {0: '/1', 1: '/8', 2: '/64', 3: '/1024', 4: '/4096'},
    'pidB_ISR': {0: '8 ns',   1: '64 ns',   2: '512 ns',   3: '8 us',   4: '6 us',   5: '524 us',   6: '8 ms',   7: '67 ms',   8: '537 ms',   9: '9 s'},
    'pidB_DSR': {0: '7.5 ns',   1: '60 ns',   2: '480 ns',   3: '7.68 us',   4: '61.44 us',   5: '491.5 us'},
    'pidB_SAT': {0: '±122uV',   1: '±244uV',   2: '±488uV',   3: '±977uV',   4: '±2mV',   5: '±4mV',   6: '±8mV',   7: '±16mV',   8: '±31mV',   9: '±62mV',   10: '±125mV',   11: '±250mV',   12: '±500mV',   13: '±1 V'},
    'stream_rate': {64: '1.95 MS/s',   128: '0.98 MS/s',   256: '488 kS/s',   512: '244 kS/s',   1024: '122 kS/s',   8192: '15 kS/s',   65536: '1.9 kS/s'}
}













class Lock():
    """
    Class for direct acces to FPGA registers.
    """
    
    def __init__(self, url, reg=None):
        self.url  = url
        self._cmd = 'lock'
        
        if reg is None:
            res = requests.get(f'{self.url}/c/{self._cmd}.txt',{})
            
            if not res.ok:
                raise ValueError('The URL is not correct')
            
            data = [ dd.split(',') for dd in  res.text.split('\n') if len(dd)>0 ]
            data.pop(0)
            
            self._registers = {}
            for dd in data:
                self._registers[dd[0]] = [int(dd[1]) , bool(int(dd[2])), bool(int(dd[3])), int(dd[4]), int(dd[5]) ]
            
        else:
            self._registers = reg
        
        self._reg_labels = reg_labels
        
        self.__doc__ += '\nBelow there are the accesible registers. Starred names are Read Only registers. Allowed values are expresed in brackets\n\n'
        for k,v in self._registers.items():
             self.__doc__ +=  f'   {"*" if v[2] else " "}{k:20s}  [{v[3]:12d} to {v[4]:<12d}]\n'
            
    def __repr__(self):
        return f"lock({self.url})"
    
    def get(self,names=None):
        """
        Method for getting registers values
        
        names can be:
            - register name: returns the value
            - string with comma or space separated register names: returns dictionary with returned values
            - list of register names: returns dictionary
            - nothing: returns dictionary with all available registers
        """
        
        if type(names) == str:
            if ',' in names:
                names = names.split(',')
            elif ' ' in names:
                names = names.split(' ')
            else:
                res = requests.get(f'{self.url}/{self._cmd}', {names : ''} ).text.strip()
                if 'ERROR' in res:
                    raise ValueError(res)
                return int(res.split(':')[1])
        
        
        names = { '': '' } if names is None else { name: '' for name in names }
        
        res = requests.get(f'{self.url}/{self._cmd}', names ).text.strip()
        
        if 'ERROR' in res:
            raise ValueError(res)
        
        return { dd.split(':')[0] : int(dd.split(':')[1]) for dd in res.split('\n') }
    
    def set(self, name, value=0 ):
        """
        Method for setting registers values
        
        if name is a register name, it sets it to value
        
        if name is a dictionary, for each key ad regname sets its value
        
        returns the value or dict of values after assigment
        """
        
        if type(name) == dict:
            res = requests.get(f'{self.url}/{self._cmd}', name ).text.strip()
            if 'ERROR' in res:
                raise ValueError(res)
            
            return { dd.split(':')[0] : int(dd.split(':')[1]) for dd in res.split('\n') }
        elif type(name) == str:
            
            if type(value) == str and name in self._reg_labels.keys():
                value = [ k for k,v in self._reg_labels[name].items() if v==value ][0]
                
            res = requests.get(f'{self.url}/{self._cmd}', {name : value} ).text.strip()
            if 'ERROR' in res or not ( ':' in res ):
                raise ValueError(f'Error was found. RP response:\n{res}\n')
            
            return int(res.split(':')[1])

    def __setattr__(self, name, value):
        # print('__setattr__')
        if name in ['url' , '_cmd' , '_registers']: # for proetection
            self.__dict__[name] = value
        elif name in self.__dict__.get('_registers').keys() :
            self.set(name,value)
        else:
            self.__dict__[name] = value

    def __getattr__(self, name):
        # print('__getattr__')
        if name in ['url' , '_cmd' , '_registers']: # for proetection
            return self.__dict__[name]
        elif name in self.__dict__.get('_registers').keys() :
            return self.get(name)
        else:
            return self.__dict__[name]
        
    def __dir__(self):
        # This is just for autocompletion inIPython
        return list(self.__dict__.keys())+list(self._registers.keys())

# l = lock('http://rp-f00a3b.local/lock_in+pid_harmonic')


#    
#    l.get(['pidA_sw','cos_ref'])
#    
#    l.get('cos_ref')
#    
#    # l.get('pepe')
#    
#    
#    l.set('oscA_sw', 3 )
#    
#    l.set(dict(oscA_sw=1,oscB_sw=2) )




#% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


class Osc():
    """
    This class is used to control Oscilloscope module registers
    """
    
    def __init__(self, url, parent=None, reg=None):
        self.url  = url
        self._cmd = 'osc'
        
        if reg is None:
            res = requests.get(f'{self.url}/c/{self._cmd}.txt',{})
            
            if not res.ok:
                raise ValueError('The URL is not correct')
            
            data = [ dd.split(',') for dd in  res.text.split('\n') if len(dd)>0 ]
            data.pop(0)
            
            self._registers = {}
            for dd in data:
                self._registers[dd[0]] = [int(dd[1]) , bool(int(dd[2])), bool(int(dd[3])), int(dd[4]), int(dd[5]) ]
        else:
            self._registers= reg
        
        self._parent = parent
        
        self.__doc__ += '\nBelow there are the accesible registers. Starred names are Read Only registers. Allowed values are expresed in brackets\n\n'
        for k,v in self._registers.items():
             self.__doc__ +=  f'   {"*" if v[2] else " "}{k:20s}  [{v[3]:12d} to {v[4]:<12d}]\n'

    def __repr__(self):
        return f"lock({self.url})"
    
    def get(self,names=None):
        """
        Method for getting registers values
        
        names can be:
            - register name: returns the value
            - string with comma or space separated register names: returns dictionary with returned values
            - list of register names: returns dictionary
            - nothing: returns dictionary with all available registers
        """
        
        if type(names) == str:
            if ',' in names:
                names = names.split(',')
            elif ' ' in names:
                names = names.split(' ')
            else:
                res = requests.get(f'{self.url}/{self._cmd}', {names : ''} ).text.strip()
                if 'ERROR' in res:
                    raise ValueError(res)
                return int(res.split(':')[1])
        
        
        names = { '': '' } if names is None else { name: '' for name in names }
        
        res = requests.get(f'{self.url}/{self._cmd}', names ).text.strip()
        
        if 'ERROR' in res:
            raise ValueError(res)
        
        return { dd.split(':')[0] : int(dd.split(':')[1]) for dd in res.split('\n') }
    
    def set(self, name, value=0 ):
        """
        Method for setting registers values
        
        if name is a register name, it sets it to value
        
        if name is a dictionary, for each key ad regname sets its value
        
        returns the value or dict of values after assigment
        """
        
        if type(name) == dict:
            res = requests.get(f'{self.url}/{self._cmd}', name ).text.strip()
            if 'ERROR' in res:
                raise ValueError(res)
            
            return { dd.split(':')[0] : int(dd.split(':')[1]) for dd in res.split('\n') }
        elif type(name) == str:
            res = requests.get(f'{self.url}/{self._cmd}', {name : value} ).text.strip()
            if 'ERROR' in res:
                raise ValueError(res)
            return int(res.split(':')[1])

    def __setattr__(self, name, value):
        # print('__setattr__')
        if name in ['url' , '_cmd' , '_registers']: # for proetection
            self.__dict__[name] = value
        elif name in self.__dict__.get('_registers').keys() :
            self.set(name,value)
        else:
            self.__dict__[name] = value

    def __getattr__(self, name):
        # print('__getattr__')
        if name in ['url' , '_cmd' , '_registers']: # for proetection
            return self.__dict__[name]
        elif name in self.__dict__.get('_registers').keys() :
            return self.get(name)
        else:
            return self.__dict__[name]
        
    def __dir__(self):
        # This is just for autocompletion inIPython
        return list(self.__dict__.keys())+list(self._registers.keys())


    def dump(self):
        res = requests.get(f'{self.url}/{self._cmd}', {'dump' : ''} ).text.strip()
        
        res = [ dd.strip().split(':') for dd in res.split('\n') ]
        
        chA = [ int(dd[1]) for dd in res if len(dd) == 3 ]
        chB = [ int(dd[2]) for dd in res if len(dd) == 3 ]
        
        rta = { dd[0] : int(dd[1]) for dd in res if len(dd) == 2 }
        
        rta['chA'] = chA #np.array(chA,dtype=np.int16)
        rta['chB'] = chB #np.array(chB,dtype=np.int16)
        
        self._parent._last_osc_dump = rta
        return rta

    def curv(self, data=None , raw=True ):
        if data is None:
            data = self.dump()
        elif data=='last':
            data = self._parent._last_osc_dump
        
        chA = data['chA']
        chB = data['chB']
        
        
        CurWpt = ( data['CurWpt']+1) % 16384
        TrgWpt = data['TrgWpt']
        
        chA = chA[CurWpt:]+chA[:CurWpt]
        chB = chB[CurWpt:]+chB[:CurWpt]
        
        
        
        TrgPosition = TrgWpt-CurWpt
        if TrgPosition<0:
            TrgPosition += 2**14
        
        ii  = np.arange(len(data['chA'])) - TrgPosition
        tt  = ii*8e-9*data['Dec']
        
        if raw:
            chA = np.array(chA,dtype=np.int16)
            chB = np.array(chB,dtype=np.int16)
        else:
            # value_in_V = (val_int+FE_CH1_DC_offs)/2**13 * FE_CH1_FS_G_HI/2**32*100
            chA = (np.array(chA,dtype=np.float)+self._parent.calib['FE_CH1_DC_offs'])*self._parent.calib['FE_CH1_FS_G_HI']*100/2**32/2**13
            chB = (np.array(chB,dtype=np.float)+self._parent.calib['FE_CH2_DC_offs'])*self._parent.calib['FE_CH2_FS_G_HI']*100/2**32/2**13
            
        return tt , chA , chB

    
    def measure(self,trig_channel, dec=1, trig_pos=0,  threshold=0 , hysteresis=63, average=False , wait=False, timeout=10):
        """
        Prepares de Oscilloscope for triggered measurement
            - trig_channel is the number or name of the trigger channel
              Should be 1 to 7 or one of these:
                 'manual','A_rising','A_falling','B_rising','B_falling','ext_rising','ext_falling'
            - trig_pos position of the trigger on the final adquisition
                can be a float between 0 and 1 or an int between 0 and 16383
            - dec is decimation: should be some of the pre-definead values
                Sample rate will be: 1/(dec*8 ns)
            - threshold: trigger level. Default is 0
            - hysteresis: to avoid noise trigger. Default is 63 int
            - average: set or not average inside decimation period.
        
        A suscesfull measurement will turn conf = 4
        """
        
        trigger_values = ['','manual','A_rising','A_falling','B_rising','B_falling','ext_rising','ext_falling']
        
        if type(trig_channel) == str:
            TrgSrc=-1
            try:
                TrgSrc = trigger_values.index(trig_channel)
            except ValueError:
                for jj,val in enumerate(trigger_values):
                    if trig_channel == val[:len(trig_channel)]:
                        TrgSrc=jj
                        break
                if TrgSrc<0:
                    raise ValueError('Trigger channel should be one of this: ' + ','.join(trigger_values[1:]))
        
        params = {}
        self.conf = 2
        sleep(0.05)
        
        if trig_channel[0]=='A':
            params['ChAth']  = threshold
            params['ChAHys'] = hysteresis
        
        if trig_channel[0]=='B':
            params['ChBth']  = threshold
            params['ChBHys'] = hysteresis
        
        params['Dec']       = dec
        if type(trig_pos) == float and trig_pos>=0 and trig_pos<=1:
            trig_pos = int(round( trig_pos* (16383) ))
        else:
            if trig_pos<0 or trig_pos>16383:
                raise ValueError('trig_pos shoult be between 0 and 16383')
                
        params['TrgDelay']  = 16384-trig_pos  # acquisitions after trigger
        
        
        
        res = requests.get(f'{self.url}/{self._cmd}', params ).text.strip()
        if 'ERROR' in res:
            raise ValueError(res)
        
        #res = requests.get(f'{self.url}/{self._cmd}', dict(conf=self.conf|1 ,TrgSrc=TrgSrc) )
        
        self.conf = 1
        sleep(trig_pos*8e-9*dec*1.2)
        self.TrgSrc = TrgSrc
        
        t0 = time()
        if wait:
            while(True):
                if self.TrgSrc == 0 and self.conf & 7 == 0:
                    break
                sleep(0.1)
                if time()-t0 > timeout:
                    raise ValueError(f'Time out reached: {timeout} sec')

        return True
        

# osc = Osc('http://rp-f00a3b.local/lock_in+pid_harmonic')


#    
#    data = osc.dump()
#    
#    
#    tt , ch1 , ch2 = osc.curv()
#    
#    
#    plt.clf()
#    plt.plot(tt,ch1,tt,ch2)



#% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


class RedPitayaApp():
    def __init__(self, url, name=None):
        
        if os.path.isfile(url):
            
            data = np.load(url,allow_pickle=True).tolist()
            
            self.url      = data['url']
            self.calib    = data['calib']
            self.name     = data['name']
            
            self.lock     = Lock(self.url,               reg=data['lock_reg'])
            self.osc      = Osc(self.url , parent=self,  reg=data['osc_reg' ])
            self.filename = url
            
            if 'dump' in data.keys():
                self._last_osc_dump = data['dump']
            
        else:
            if '?' in url:
                url = url.split('?')[0]
            
            if url[-1]=='/':
                url = url[:-1]
            
            self.url = url
            
            self.lock = Lock(self.url)
            self.osc  = Osc(self.url,parent=self)
            
            self._get_calib()
            
            if name is None:
                name = self.url.split('/')[2]
            
            self.name     = name
            self.filename = None
        
        self.__doc__ = """
            Class to control Red Pitaya lock-in+pid Harmonic
            
            The lock-in      registers can be accessed throught {rp}.lock
            The oscilloscipe registers can be accessed throught {rp}.osc
            
            Usefull functions and objects:
                
                {rp}.url                                 : url of the Red Pitaya App
                {rp}.calib                               : Calibration information for Voltage conversion
                {rp}.streaming_*                         : streamign related functions
                {rp}.save_params() / {rp}.load_params()  : Save/Load RP regs state
                
                {rp}.osc.measure()                       : Acquire oscilloscope channels
                {rp}.save_last_meas()                    : Save last acquired data
                {rp}.wait_osc_finish()                   : wait until acquisition is finished
                {rp}.plot_meas()                         : Fast plot of last acquisition
                
                {rp}.set_lpf()                           : Configure Low Pass Filters values
                {rp}.get_lpf()                           : Show Low Pass Filters values in human readble format
                {rp}.get_XY()                            : Get demodulated values from lock-in module
            
            """
        self.__doc__ = self.__doc__.replace('{rp}',self.name )
        
    def __repr__(self):
        return f'RedPitayaApp({self.name})'

    def _get_calib(self):
        """
        Internal function to load calibration values
        """
        res = requests.get(f'{self.url}/calib', {} ).text.strip()
        
        self.calib = { dd.split('=')[0].strip() : int(dd.split('=')[1].strip()) for dd in res.split('\n') if len(dd)>0 }
    
    
    def streaming_prepare(self):
        """
        Prepares RP for streaming
        """
        res = requests.get(f'{self.url}/streaming',{})
        if not res.ok:
            raise ValueError('The URL is not correct')
        
        return res.text.strip()
    
    def streaming_start(self):
        """
        Starts streamign of values
        """
        self.lock.stream_cmd = 1
    
    def streaming_stop(self):
        """
        Stops streamign of values
        """
        self.lock.stream_cmd = 0
    
    def save_params(self, filename=None, include_values = True, include_dump=False ):
        """
        Save actual params of RP App.
            filename       : file name to save data
            include_values : if True, includes osc and lock values
            include_dump   : if True, includes last acquired oscilloscope data
        """
        now      = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if filename is  None:
            filename = f'{now}_{self.name}_params.npy'
        
        
        data     = dict(calib     = self.calib,
                        name      = self.name,
                        url       = self.url,
                        timestamp = time(),
                        datetime  = datetime.now().isoformat(),
                        osc_reg   = self.osc._registers , 
                        lock_reg  =self.lock._registers)
        
        if include_values:
            data['osc_values' ] = self.osc.get()
            data['lock_values'] = self.lock.get()
            
        if include_dump:
            data['dump'       ] = self._last_osc_dump
        
        np.save(filename, data )
        
        return filename
    
    def load_params(self, filename = None ):
        """
        Loads saved params from filename
        """
        if filename is None:
            filename = self.filename 
        
        if not os.path.isfile(filename):
            raise ValueError(f'Filename {filename} does not exist')
        
        data = np.load( filename ,allow_pickle=True ).tolist()
        
        for key, val in data['lock_values'].items():
            if key in self.lock._registers.keys() and not self.lock._registers[key][2]:
                self.lock.set(key,val)
        
        for key, val in data['osc_values'].items():
            if key in self.osc._registers.keys() and not self.osc._registers[key][2]:
                self.osc.set(key,val)
                
    
    def set_lpf(self, tau_exponent=14, order=2 , line='ref' ):
        """
        Configure Lof Pass Filters
            tau_exponent : The characteristic time will be set to 2**tau_exponent * 8 ns. tau_exponent should be between 14 and 29
            order        : order of the filter. Could be 0 (OFF), 1 or 2
            line         : which line of demodulation will be modified. 'ref' or 0 refers to X and Y lines. 1,2,3 refers to F1, F2, F3 lines.
        """
        if tau_exponent>30 or tau_exponent<14:
            raise ValueError(f'tau_exponent shold be between 14 and 29')
        if order>2 or order<0:
            raise ValueError(f'order should be between 0 (OFF) and 2')
            
        val  = tau_exponent -14
        val += 16*order
        
        if line[:3].lower() == 'ref':
            line = 0
            setattr(self.lock, f'lpf_F{line}' , val )
        elif line[:3].lower() == 'all':
            for line in range(3):
                setattr(self.lock, f'lpf_F{line}' , val )
        
        print(f'LPF was set to 8 ns * 2**{tau_exponent} = { int(round(8*2**14/1000)) } us , order {order}')
        return 8e-9*2**val
    
    def get_lpf(self,line=None):
        """
        Shows Lof Pass Filters in Human readable format
            line: which line of demodulation will be shown. 'ref' or 0 refers to X and Y lines. 1,2,3 refers to F1, F2, F3 lines.
        """
        print('Values of Low Pass Filters in Human readable numbers (order 0 is OFF):')
        
        
        lpfs = [self.lock.lpf_F0,self.lock.lpf_F1,self.lock.lpf_F2,self.lock.lpf_F3]
        
        if line is None:
            for lpf,name in zip(lpfs, 'ref F1 F2 F3'.split()):
                val   = (lpf & 31) + 14
                order = int( ( lpf & 48 ) /16 )
                print(f'{name:4s}: is set to 2**{val:<2d} * 8 ns = {8e-9*2**val} seg , order={order} ')
        elif type(line)==int :
            lpf = lpfs[line]
            val   = (lpf & 31) + 14
            order = int( ( lpf & 48 ) /16 )
            
            return  8e-9*2**val , order 
    
    def get_XY(self,units='V',F=False):
        """
        Get values of lock-in registers.
            units  :  'V' is Volts. Anything else is 'int' values.
            F      : if False, returs X and Y . If True, returns X, Y, F1, F2, F3
        """
        offset = 0
        gain   = 1.0/2**13/2**11
                
        if units.lower()[0]=='v':
            input_signal = self.lock.signal_sw
            if input_signal in [0,1]:
                offset = self.calib[f'FE_CH{input_signal+1}_DC_offs']
                gain   = self.calib[f'FE_CH{input_signal+1}_FS_G_HI']*100/2**45/2**11
        else:
            gain = 1.0/2**11
        
        read_ctrl           = self.lock.read_ctrl
        self.lock.read_ctrl = read_ctrl | 1 
        X, Y = (offset+self.lock.X_28)*gain , (offset+self.lock.Y_28)*gain
        if F:
            F1, F2, F3 = (offset+self.lock.F1_28)*gain , (offset+self.lock.F2_28)*gain ,  (offset+self.lock.F3_28)*gain
        self.lock.read_ctrl = read_ctrl
        
        if F:
            return np.array([X, Y, F1, F2, F3])
        else:
            return np.array([X, Y])
    
    def get_freq(self):
        """
        Returns the lock-in base modulation frequency in Hz
        """
        return 1.0/(  (self.lock.gen_mod_hp+1)*2520*8e-9  )
    
    def get_period(self):
        """
        Returns the lock-in base modulation period in sec
        """
        return (self.lock.gen_mod_hp+1)*2520*8e-9 
    
    def set_freq(self, val ):
        """
        Sets the frequency value by setting the 'val' value (in ints) to the lock.gen_mod_hp register.
        Returns the frequency set in Hz
        
            val  : integer to assign to gen_mod_hp. Can be between 0 to 16383
        """
        self.lock.gen_mod_hp = val
        return self.get_freq()
        
        
    def set_modulation_amplitud(self,val,ch='out1'):
        """
        Sets the amplitude of modulation over an specific output channel. It's equivalent 
        to setting the lock.mod_out[1,2] register to that value.
        Returns the modulation amplitude in Volts.
            val  : integer from -1 to 8191 . -1 means OFF. 0 is 0 Volts amplitude. 8192 ints equals to 1 Volt.
            ch   : channel. Can be 'out1' or 'out2'
        """
        
        if val<-1 or val>8191:
            raise ValueError(f'val wrong value. Values should be from -1 to 8191. You tryed to set: {val}')
        
        if not ch.lower() in ['out1','out2']:
            raise ValueError(f"ch wrong value. Should be 'out1' or 'out2'. You set: {ch}")
        
        setattr(self, 'mod_out'+ch[-1] , val )
        
        return float(val)/8192/2
    
    
    def set_phase(self,val):
        """
        Sets the phase value by setting the 'val' value (in ints) to the lock.gen_mod_phase register.
        The value representa the de-phasing of cos_ref vs cos_1f (and also cos_2f and cos_3f).
        Returns the phase in degrees
        
            val  : integer to assign to gen_mod_phase. Can be between 0 to 2519. 2520 represents 360°
        """
        
        if val<0 or val>2519:
            raise ValueError(f'val wrong value. Values should be from 0 to 2519. You tryed to set: {val}')
        
        self.lock.gen_mod_phase = val
        
        return float(val)/2520*360
    
    def save_last_meas(self,filename=None, include_values = True ):
        """
        Saves last acquisitions values
            filename       : file name to save data.
            include_values : if True, includes other registers values
        """
        return self.save_params(filename=filename, include_values = include_values, include_dump=True )
    
    
    def wait_osc_finish(self, timeout=60):
        """
        Waits until acquisition is finished.
            timeout : timeout in seconds
        """
        
        t0 = time()
        while self.osc.TrgSrc>0:
            print('.',end='')
            sleep(0.1)
            if time()-t0 > timeout:
                raise ValueError('Timeout')
        print('\n')
        return 0
    
    def plot_meas(self, filename=None , raw=False ):
        """
        Fast plot of acquisition.
            filename : if None, plot last acquisition. If filename path, plot saved data.
            raw      : if True, use int instead of Volts as units.
        """
        if filename is None:
            data = self._last_osc_dump
            if self.filename is None:
                data['lock_values'] = self.lock.get()
        elif os.path.isfile(filename):
            data = np.load( filename ,allow_pickle=True ).tolist()['dump']

        tt, ch1, ch2 = self.osc.curv( data=data , raw=raw )
        
        from matplotlib import pyplot as plt
        
        fig, ax = plt.subplots( 2,1, figsize=(13,7) ,  constrained_layout=True , sharex=True )
        
        ax[0].plot( tt, ch1 )
        ax[1].plot( tt, ch2 )
        ax[1].set_xlabel('time [sec]')
        
        label1 = label2 = ''
        if 'lock_values' in data.keys():
            label1 = self.lock._reg_labels['oscA_sw'][ data['lock_values']['oscA_sw'] ] + ' '
            label2 = self.lock._reg_labels['oscB_sw'][ data['lock_values']['oscB_sw'] ] + ' '
        
        ax[0].set_ylabel(f'ch1 {label1}[V]')
        ax[1].set_ylabel(f'ch2 {label2}[V]')
        
        for aa in ax:
            aa.grid(b=True,linestyle= '--',color='lightgray')
        
    
# rp = RedPitayaApp('med00.npy')





# rp = RedPitayaApp('http://rp-f00a3b.local/lock_in+pid_harmonic/?type=run')


# rp.save_params('med00.npy')



#rp.osc.measure('ext', dec=1 , trig_pos=8191 )

#rp.osc.dump()


# rp.plot_meas()

#    rp.osc.measure('B_ri', dec=1024 , trig_pos=8191 , hysteresis=1, threshold=5000)

#
#    
#    for jj in range(10000):
#        print(rp.osc.TrgSrc , rp.osc.conf )
#        
#        if rp.osc.TrgSrc == 0 and rp.osc.conf & 7 == 0:
#            break
#    
#    sleep(0.1)

#
#rp.osc.measure('B_ri', dec=1024 , trig_pos=8191 , hysteresis=1, threshold=5000, wait=True)
#
#tt , ch1 , ch2 = rp.osc.curv(raw=False)
#
#plt.figure()
#plt.plot(tt,ch1,tt,ch2)
#plt.gca().axvline(0, color='gray' , alpha=0.5)
#
#
#





#%%



"""
import bs4

# h    = bs4.BeautifulSoup( requests.get('http://rp-f00a3b.local/lock_in+pid_harmonic/').text , "lxml")

h    = bs4.BeautifulSoup( requests.get('http://192.168.1.117/lock_in+pid_harmonic/').text , "lxml")



reg_labels = {}

for reg in rp.lock._registers.keys() :
    aa = h.select_one(f'#lock_{reg}')
    if hasattr(aa,'name') and aa.name=='select':
        print(reg)
        reg_labels[reg] = { int(d.attrs['value']) :d.getText() for d in aa.select('option') }


"""































