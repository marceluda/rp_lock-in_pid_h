#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Library for remote control of Lock-in+PID App on RedPitaya
"""



#%%





import requests
import numpy as np

url = "http://rp-f00a3b.local/lock_in+pid_harmonic/?type=run"


if '?' in url:
    url = url.split('?')[0]

if not url[-1]=='/':
    url += '/'




res = requests.get(url+'c/osc.txt',{})

if not res.ok:
    raise ValueError('The URL is not correct')


Parameter = namedtuple('Parameter', 'name index signed read_only min max')

data = [ dd.split(',') for dd in  res.text.split('\n') if len(dd)>0 ]
data.pop(0)


registers = {}
for dd in data:
    registers[dd[0]] = [int(dd[1]) , bool(dd[2]), bool(dd[3]), int(dd[4]), int(dd[5]) ]



#%% Class for lock module




class Lock():
    """
    This class is used to control lock module registers
    """
    
    def __init__(self, url):
        self.url  = url
        self._cmd = 'lock'
        
        res = requests.get(f'{self.url}/c/{self._cmd}.txt',{})
        
        if not res.ok:
            raise ValueError('The URL is not correct')
        
        data = [ dd.split(',') for dd in  res.text.split('\n') if len(dd)>0 ]
        data.pop(0)
        
        self._registers = {}
        for dd in data:
            self._registers[dd[0]] = [int(dd[1]) , bool(dd[2]), bool(dd[3]), int(dd[4]), int(dd[5]) ]
            #self.__dict__[dd[0]]   = 0

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





#%%





class Osc():
    """
    This class is used to control Oscilloscope module registers
    """
    
    def __init__(self, url):
        self.url  = url
        self._cmd = 'osc'
        
        res = requests.get(f'{self.url}/c/{self._cmd}.txt',{})
        
        if not res.ok:
            raise ValueError('The URL is not correct')
        
        data = [ dd.split(',') for dd in  res.text.split('\n') if len(dd)>0 ]
        data.pop(0)
        
        self._registers = {}
        for dd in data:
            self._registers[dd[0]] = [int(dd[1]) , bool(dd[2]), bool(dd[3]), int(dd[4]), int(dd[5]) ]
            #self.__dict__[dd[0]]   = 0

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
        return rta

    def curv(self, data=None , raw=True ):
        if data is None:
            data = self.dump()
        
        chA = data['chA']
        chB = data['chB']
        
        
        CurWpt = ( data['CurWpt']+1) % 16384
        TrgWpt = data['TrgWpt']
        
        chA = chA[CurWpt:]+chA[:CurWpt]
        chB = chB[CurWpt:]+chB[:CurWpt]
        
        chA = np.array(chA,dtype=np.int16)
        chB = np.array(chB,dtype=np.int16)
        
        ii  = np.arange(len(data['chA'])) - (TrgWpt-CurWpt)
        tt  = ii*8e-9*data['Dec']
        
        return tt , chA , chB
        


osc = Osc('http://rp-f00a3b.local/lock_in+pid_harmonic')



data = osc.dump()


tt , ch1 , ch2 = osc.curv()

#    
#    
#    plt.clf()
#    plt.plot(tt,ch1,tt,ch2)


#%%




#%%

if __name__ == '__main__':
    pass
