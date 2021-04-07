#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Library for remote control of Lock-in+PID App on RedPitaya
"""



#%%



import requests
import numpy as np
from time import sleep,time


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
            self._registers[dd[0]] = [int(dd[1]) , bool(int(dd[2])), bool(int(dd[3])), int(dd[4]), int(dd[5]) ]
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




#% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


class Osc():
    """
    This class is used to control Oscilloscope module registers
    """

    def __init__(self, url, parent=None):
        self.url  = url
        self._cmd = 'osc'

        res = requests.get(f'{self.url}/c/{self._cmd}.txt',{})

        if not res.ok:
            raise ValueError('The URL is not correct')

        data = [ dd.split(',') for dd in  res.text.split('\n') if len(dd)>0 ]
        data.pop(0)

        self._registers = {}
        for dd in data:
            self._registers[dd[0]] = [int(dd[1]) , bool(int(dd[2])), bool(int(dd[3])), int(dd[4]), int(dd[5]) ]
            #self.__dict__[dd[0]]   = 0

        self._parent = parent

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
                if rp.osc.TrgSrc == 0 and rp.osc.conf & 7 == 0:
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
    def __init__(self, url):

        if '?' in url:
            url = url.split('?')[0]

        if url[-1]=='/':
            url = url[:-1]

        self.url = url

        self.lock = Lock(self.url)
        self.osc  = Osc(self.url,parent=self)

        self._get_calib()

    def __repr__(self):
        return f'RedPitayaApp({self.url})'

    def _get_calib(self):
        res = requests.get(f'{self.url}/calib', {} ).text.strip()

        self.calib = { dd.split('=')[0].strip() : int(dd.split('=')[1].strip()) for dd in res.split('\n') if len(dd)>0 }


rp = RedPitayaApp('http://rp-f00a3b.local/lock_in+pid_harmonic/?type=run')




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

if __name__ == '__main__':
    pass
