#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Library for remote control of Lock-in+PID App on RedPitaya

Remote control of the "Harmonic Lock-in+PID" App (lock_in+pid_harmonic) over HTTP, through the
endpoints /lock, /osc and /calib of the App (see nginx.conf and doc/Remote.md).

Needs: requests, numpy (and matplotlib for plot_meas()).

v2.3.15 (Ecosystem 2.0, FPGA of v2.3.15):
  - Oscilloscope: the 2.0 scope locks its trigger after every trigger (TrgSrc bit 5) until 1 is
    written to TrgUnlock (offset 0x94). Osc.measure() unlocks it before setting the trigger source,
    and the end of the acquisition is detected as the C controller does (src/fpga.c
    osc_fpga_triggered()): conf bit 4 (2.0), or TrgSrc == 0 and conf bit 2 == 0 (0.9x).
  - Lock control (v2.3.13): lock_control is command + configuration, lock_status is read only.
    See lock_config(), lock_launch(), lock_now(), lock_release(), lock_status().
  - PID, ramp and lock-in helpers: set_pid(), set_ramp(), set_manual(), set_signal(), set_gain(),
    set_lpf(), set_phase(), set_freq_hz().
  - Works with current NumPy (no np.float) and Matplotlib (no grid(b=...)).

The arguments of one HTTP request reach c/lock and c/osc in a non guaranteed order (Lua table):
writes whose order matters are done with one request each.
"""



#%%



import requests
import numpy as np
from time import sleep,time


from datetime import datetime


import os
import warnings



# Timeout of each HTTP request [s]
HTTP_TIMEOUT = 10

# Clock of the FPGA: 125 MHz
TICK = 8e-9


#%% Class for lock module

reg_labels = {
    'oscA_sw': {0: '0',   1: 'in1',   2: 'in2',   3: 'error',   4: 'ctrl_A',   5: 'ctrl_B',   6: 'Ramp A',   7: 'Ramp B',   8: 'pidA_in',   9: 'pidB_in',   10: 'PID A out',   11: 'PID B out',   12: 'sin_ref',   13: 'cos_ref',   14: 'cos_1f',   15: 'cos_2f',   16: 'cos_3f',   17: 'Xo',   18: 'Yo',   19: 'F1o',   20: 'F2o',   21: 'F3o',   22: 'signal_i',   23: 'out1',   24: 'out2'},
    'oscB_sw': {0: '0',   1: 'in1',   2: 'in2',   3: 'error',   4: 'ctrl_A',   5: 'ctrl_B',   6: 'Ramp A',   7: 'Ramp B',   8: 'pidA_in',   9: 'pidB_in',   10: 'PID A out',   11: 'PID B out',   12: 'sin_ref',   13: 'cos_ref',   14: 'cos_1f',   15: 'cos_2f',   16: 'cos_3f',   17: 'Xo',   18: 'Yo',   19: 'F1o',   20: 'F2o',   21: 'F3o',   22: 'signal_i',   23: 'out1',   24: 'out2'},
    'trig_sw': {0: 'None',   1: 'Pin',   2: 'Scan floor',   4: 'Scan ceil',   8: 'harmonic mod.',   16: 'Square mod.',   32: 'Out of lock',   64: 'Jump trigger',   128: 'Lock control trig'},
    'out1_sw': {0: '0',   1: 'in1',   2: 'in2',   3: 'in1-in2',   4: 'error',   5: 'cos_1f',   6: 'cos_2f',   7: 'cos_3f',   8: 'cos_ref',   9: 'sin_ref',   10: 'PID A out',   11: 'PID B out',   12: 'ctrl_A',   13: 'ctrl_B',   14: 'aux_A',   15: 'aux_B'},
    'out2_sw': {0: '0',   1: 'in1',   2: 'in2',   3: 'in1-in2',   4: 'error',   5: 'cos_1f',   6: 'cos_2f',   7: 'cos_3f',   8: 'cos_ref',   9: 'sin_ref',   10: 'PID A out',   11: 'PID B out',   12: 'ctrl_A',   13: 'ctrl_B',   14: 'aux_A',   15: 'aux_B'},
    'lock_trig_sw': {0: 'error',   1: 'Xo',   2: 'Yo',   3: 'F1o',   4: 'F2o',   5: 'F3o',   6: '0 (sqXo)',   7: '0 (sqYo)',   8: '0 (sqFo)',   9: 'signal_i',   10: 'Ramp A',   11: 'aux_A',   12: 'in1',   13: 'in2',   14: 'in1-in2',   15: 'PID A out'},
    'rl_signal_sw': {0: 'in1',   1: 'in2',   2: 'in1-in2',   3: 'aux_A',   4: 'aux_B',   5: '0',   6: '0',   7: '0'},
    'signal_sw': {0: 'in1',   1: 'in2',   2: 'in1-in2',   3: 'cos_ref',   4: 'sin_ref',   5: 'cos_1f',   6: 'aux_A',   7: 'Ramp A'},
    'sg_amp0': {0: 'x1',   1: 'x2',   2: 'x4',   3: 'x8',   4: 'x16',   5: 'x32',   6: 'x64',   7: 'x128',   8: 'x256',   9: 'x512',   10: 'x1k',   11: 'x2k',   12: 'x4k',   13: 'x8k',   14: 'x16k',   15: 'x32k',   16: 'x64k',   17: 'x128k',   18: 'x256k',   19: 'x512k'},
    'sg_amp1': {0: 'x1',   1: 'x2',   2: 'x4',   3: 'x8',   4: 'x16',   5: 'x32',   6: 'x64',   7: 'x128',   8: 'x256',   9: 'x512'},
    'sg_amp2': {0: 'x1',   1: 'x2',   2: 'x4',   3: 'x8',   4: 'x16',   5: 'x32',   6: 'x64',   7: 'x128',   8: 'x256',   9: 'x512'},
    'sg_amp3': {0: 'x1',   1: 'x2',   2: 'x4',   3: 'x8',   4: 'x16',   5: 'x32',   6: 'x64',   7: 'x128',   8: 'x256',   9: 'x512'},
    'error_sw': {0: '0',   1: 'Xo',   2: 'Yo',   3: 'F1o',   4: 'F2o',   5: 'F3o',   6: 'in1',   7: 'in1-in2'},
    'pidA_sw': {0: 'error',   1: 'Xo',   2: 'Yo',   3: 'F1o',   4: 'F2o',   5: 'F3o',   6: 'signal_i',   7: 'Ramp A',   8: 'in1-in2',   9: 'in1',   10: 'in2',   11: 'aux_A',   12: 'aux_B',   13: 'cos_ref',   14: 'sin_ref',   15: '0'},
    'pidA_PSR': {0: '/1', 1: '/8', 2: '/64', 3: '/1024', 4: '/4096'},
    'pidA_ISR': {0: '8 ns',   1: '64 ns',   2: '512 ns',   3: '8 us',   4: '65 us',   5: '524 us',   6: '8 ms',   7: '67 ms',   8: '537 ms',   9: '9 s'},
    'pidA_DSR': {0: '7.5 ns',   1: '60 ns',   2: '480 ns',   3: '7.68 us',   4: '61.44 us',   5: '491.5 us'},
    'pidA_SAT': {0: '±122uV',   1: '±244uV',   2: '±488uV',   3: '±977uV',   4: '±2mV',   5: '±4mV',   6: '±8mV',   7: '±16mV',   8: '±31mV',   9: '±62mV',   10: '±125mV',   11: '±250mV',   12: '±500mV',   13: '±1 V'},
    'pidB_sw': {0: 'error',   1: 'Xo',   2: 'Yo',   3: 'F1o',   4: 'F2o',   5: 'F3o',   6: 'signal_i',   7: 'Ramp A',   8: 'in1-in2',   9: 'in1',   10: 'in2',   11: 'aux_A',   12: 'aux_B',   13: 'cos_ref',   14: 'sin_ref',   15: '0'},
    'pidB_PSR': {0: '/1', 1: '/8', 2: '/64', 3: '/1024', 4: '/4096'},
    'pidB_ISR': {0: '8 ns',   1: '64 ns',   2: '512 ns',   3: '8 us',   4: '65 us',   5: '524 us',   6: '8 ms',   7: '67 ms',   8: '537 ms',   9: '9 s'},
    'pidB_DSR': {0: '7.5 ns',   1: '60 ns',   2: '480 ns',   3: '7.68 us',   4: '61.44 us',   5: '491.5 us'},
    'pidB_SAT': {0: '±122uV',   1: '±244uV',   2: '±488uV',   3: '±977uV',   4: '±2mV',   5: '±4mV',   6: '±8mV',   7: '±16mV',   8: '±31mV',   9: '±62mV',   10: '±125mV',   11: '±250mV',   12: '±500mV',   13: '±1 V'},
    'stream_rate': {64: '1.95 MS/s',   128: '0.98 MS/s',   256: '488 kS/s',   512: '244 kS/s',   1024: '122 kS/s',   8192: '15 kS/s',   65536: '1.9 kS/s'}
}

# Old label of pidX_ISR = 4 (typo of the UI before v2.3.15), still accepted by set()
_label_alias = {'6 us': '65 us'}



class AcquisitionTimeout(TimeoutError, ValueError):
    """Timeout waiting for an acquisition or a lock (also a ValueError, as in the old versions)."""
    pass



def _to_int(value):
    """Integer value for c/lock and c/osc (nginx only passes integers: '5.0' would be ignored)"""
    if isinstance(value, (bool, np.bool_)):
        return int(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)) and float(value).is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().lstrip('-').isdigit():
        return int(value)
    raise ValueError(f'Only integer values can be written. You tried: {value!r}')


def _parse_regs(txt):
    """Parse the 'name:value' lines of c/lock and c/osc"""
    rta = {}
    for dd in txt.strip().split('\n'):
        dd = dd.strip()
        if dd.count(':') == 1:
            k, v = dd.split(':')
            rta[k.strip()] = int(v)
    return rta


def _http_get(url, params=None):
    """GET with timeout. Raises ValueError on HTTP errors and on 'ERROR' answers of c/lock, c/osc"""
    res = requests.get(url, params if params is not None else {}, timeout=HTTP_TIMEOUT)
    if not res.ok:
        raise ValueError(f'HTTP {res.status_code} from {res.url}')
    txt = res.text.strip()
    if 'ERROR' in txt:
        raise ValueError(f'Error was found. RP response:\n{txt}\n')
    return txt



class _Registers():
    """
    Common part of Lock and Osc: direct access to the FPGA registers through c/<cmd> over HTTP.
    """

    _protected = ['url', '_cmd', '_registers', '_reg_labels', '_parent']

    def __init__(self, url, cmd, reg=None, labels=None):
        self.url  = url
        self._cmd = cmd

        if reg is None:
            res = requests.get(f'{self.url}/c/{self._cmd}.txt', {}, timeout=HTTP_TIMEOUT)

            if not res.ok:
                raise ValueError('The URL is not correct')

            data = [ dd.strip().split(',') for dd in  res.text.split('\n') if len(dd.strip())>0 ]
            data.pop(0)

            registers = {}
            for dd in data:
                registers[dd[0]] = [int(dd[1]) , bool(int(dd[2])), bool(int(dd[3])), int(dd[4]), int(dd[5]) ]
            self._registers = registers
        else:
            self._registers = reg

        self._reg_labels = labels if labels is not None else {}

        self.__doc__ = (type(self).__doc__ or '') + '\nBelow there are the accesible registers. Starred names are Read Only registers. Allowed values are expresed in brackets\n\n'
        for k,v in self._registers.items():
             self.__doc__ +=  f'   {"*" if v[2] else " "}{k:20s}  [{v[3]:12d} to {v[4]:<12d}]\n'

    def __repr__(self):
        return f"{self._cmd}({self.url})"

    def _value(self, name, value):
        """Integer value of a register, translating labels (e.g. oscA_sw='cos_ref')"""
        if isinstance(value, str) and name in self._reg_labels:
            value = _label_alias.get(value, value)
            keys = [ k for k,v in self._reg_labels[name].items() if v==value ]
            if len(keys)==0:
                raise ValueError(f'"{value}" is not a label of {name}. Labels: ' +
                                 ', '.join(f'{k}: "{v}"' for k,v in self._reg_labels[name].items()))
            return keys[0]
        return _to_int(value)

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
                names = [ n.strip() for n in names.split(',') if n.strip() ]
            elif ' ' in names.strip():
                names = names.split()
            else:
                rta = _parse_regs(_http_get(f'{self.url}/{self._cmd}', {names.strip() : ''} ))
                if names.strip() not in rta:
                    raise ValueError(f'No value read for {names}')
                return rta[names.strip()]

        names = { '': '' } if names is None else { name: '' for name in names }

        return _parse_regs(_http_get(f'{self.url}/{self._cmd}', names ))

    def set(self, name, value=0 ):
        """
        Method for setting registers values

        if name is a register name, it sets it to value

        if name is a dictionary, for each key ad regname sets its value
        (the order of the writes is not guaranteed: use one call per register when it matters)

        Values can be integers or, for selectors, the labels of the web interface (reg_labels).

        returns the value or dict of values after assigment
        """

        if type(name) == dict:
            params = { k: self._value(k, v) for k,v in name.items() }
            return _parse_regs(_http_get(f'{self.url}/{self._cmd}', params ))
        elif type(name) == str:
            value = self._value(name, value)
            rta = _parse_regs(_http_get(f'{self.url}/{self._cmd}', {name : value} ))
            if name not in rta:
                raise ValueError(f'Error was found. No value read back for {name}')
            return rta[name]
        raise ValueError('name should be a register name or a dict')

    def __setattr__(self, name, value):
        # print('__setattr__')
        if name in self._protected: # for proetection
            self.__dict__[name] = value
        elif name in (self.__dict__.get('_registers') or {}).keys() :
            self.set(name,value)
        else:
            self.__dict__[name] = value

    def __getattr__(self, name):
        # print('__getattr__')
        # only called when the attribute is not found in the usual places
        if name.startswith('__') or name in self._protected:
            raise AttributeError(name)
        if name in (self.__dict__.get('_registers') or {}).keys() :
            return self.get(name)
        raise AttributeError(f'{type(self).__name__} has no register or attribute "{name}"')

    def __dir__(self):
        # This is just for autocompletion inIPython
        return list(self.__dict__.keys())+list(self._registers.keys())+[ m for m in dir(type(self)) if not m.startswith('_') ]



class Lock(_Registers):
    """
    Class for direct acces to FPGA registers.
    """

    def __init__(self, url, reg=None):
        super().__init__(url, 'lock', reg=reg, labels=reg_labels)

# l = Lock('http://rp-f00a3b.local/lock_in+pid_harmonic')


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


class Osc(_Registers):
    """
    This class is used to control Oscilloscope module registers
    """

    # conf (0x00) bits
    CONF_ARM       = 0x01   # (W) arm
    CONF_RST       = 0x02   # (W) reset of the write state machine
    CONF_TRIG_ST   = 0x04   # (R) trigger status (2.0: trigger received; 0.9x: post trigger delay running)
    CONF_ACQ_DONE  = 0x10   # (R) 2.0 only: post trigger delay over (acquisition finished)
    # TrgSrc (0x04) bits
    TRG_SRC_MASK   = 0x0f   # trigger source (0 = none / already triggered)
    TRG_LOCKED     = 0x20   # 2.0 only: trigger locked until 1 is written to TrgUnlock (0x94)

    trigger_values = ['','manual','A_rising','A_falling','B_rising','B_falling','ext_rising','ext_falling']

    def __init__(self, url, parent=None, reg=None):
        super().__init__(url, 'osc', reg=reg)
        self._parent = parent
        self._warned_no_unlock = False

    @property
    def has_unlock(self):
        """True if c/osc of the App knows the TrgUnlock register (v2.3.15 and later)"""
        return 'TrgUnlock' in self._registers

    def unlock_trigger(self):
        """
        Re-enables the trigger of the 2.0 scope, which locks itself after every trigger (TrgSrc bit 5).
        Same as the C controller (src/fpga.c osc_fpga_set_trigger()). Harmless on the 0.9x scope.
        Returns True if the unlock was written.
        """
        if self.has_unlock:
            self.set('TrgUnlock', 1)
            return True
        if not self._warned_no_unlock and (self.get('TrgSrc') & self.TRG_LOCKED):
            self._warned_no_unlock = True
            warnings.warn('The trigger of the scope is locked (TrgSrc bit 5) and c/osc of the App has no '
                          'TrgUnlock register: update the App on the Red Pitaya to v2.3.15 or later.')
        return False

    def trigger_locked(self):
        """True if the trigger of the 2.0 scope is locked (it needs unlock_trigger())"""
        return bool(self.get('TrgSrc') & self.TRG_LOCKED)

    def acq_done(self):
        """
        True when the armed acquisition has finished (trigger received and post-trigger delay elapsed).
        Same criterion as the C controller (src/fpga.c osc_fpga_triggered()):
          - 2.0 scope: conf bit 4 (post trigger delay over);
          - 0.9x scope: TrgSrc back to 0 and conf bit 2 (delay running) == 0.
        TrgSrc is read before conf, in separate requests (as the C code does).
        """
        src  = self.get('TrgSrc')
        conf = self.get('conf')
        if conf & self.CONF_ACQ_DONE:
            return True
        return ((src & self.TRG_SRC_MASK) == 0) and not (conf & self.CONF_TRIG_ST)

    def wait(self, timeout=10, poll=0.05, verbose=False):
        """
        Waits until the acquisition is finished (acq_done()).
            timeout : seconds (AcquisitionTimeout, a ValueError, if reached)
        """
        t0 = time()
        while not self.acq_done():
            if verbose:
                print('.', end='', flush=True)
            if time()-t0 > timeout:
                raise AcquisitionTimeout(f'Time out reached: {timeout} sec (no trigger?)')
            sleep(poll)
        if verbose:
            print('')
        return True

    def dump(self):
        """
        Reads both channel buffers (16384 samples each, in buffer order, 14 bit signed) and the
        registers. Also reads oscA_sw / oscB_sw of the lock module (signal of each channel).
        """
        res = _http_get(f'{self.url}/{self._cmd}', {'dump' : ''} )

        res = [ dd.strip().split(':') for dd in res.split('\n') ]

        chA = [ int(dd[1]) for dd in res if len(dd) == 3 ]
        chB = [ int(dd[2]) for dd in res if len(dd) == 3 ]

        rta = { dd[0] : int(dd[1]) for dd in res if len(dd) == 2 }

        rta['chA'] = chA #np.array(chA,dtype=np.int16)
        rta['chB'] = chB #np.array(chB,dtype=np.int16)

        if self._parent is not None:
            try:
                sw = self._parent.lock.get(['oscA_sw','oscB_sw'])
                rta['oscA_sw'] = sw['oscA_sw']
                rta['oscB_sw'] = sw['oscB_sw']
            except Exception:
                pass
            self._parent._last_osc_dump = rta
        return rta

    def _to_volts(self, ch, data, name):
        """Counts -> V. in1/in2 with the calibration of that input, other signals 8192 counts = 1 V"""
        calib = getattr(self._parent, 'calib', None) or {}
        sw = data.get(f'osc{name}_sw', data.get('lock_values', {}).get(f'osc{name}_sw', None))
        if sw is None:
            inp = 1 if name == 'A' else 2      # saved by an old version: as before
        else:
            inp = sw if sw in (1, 2) else None
        if inp is not None and f'FE_CH{inp}_FS_G_HI' in calib and f'FE_CH{inp}_DC_offs' in calib:
            # value_in_V = (val_int+FE_CH1_DC_offs)/2**13 * FE_CH1_FS_G_HI/2**32*100
            return (np.array(ch,dtype=float)+calib[f'FE_CH{inp}_DC_offs'])*calib[f'FE_CH{inp}_FS_G_HI']*100/2**32/2**13
        return np.array(ch,dtype=float)/8192

    def curv(self, data=None , raw=True ):
        """
        Returns tt, ch1, ch2 of an acquisition, oldest sample first and tt = 0 at the trigger.
            data : None (reads the buffers now, dump()), 'last' (last dump) or a dump dict
            raw  : True: int counts. False: Volts (8192 counts = 1 V; in1 / in2 with the calibration)
        """
        if data is None:
            data = self.dump()
        elif type(data) == str and data=='last':
            data = self._parent._last_osc_dump

        chA = list(data['chA'])
        chB = list(data['chB'])


        CurWpt = ( data['CurWpt']+1) % 16384
        TrgWpt = data['TrgWpt']

        chA = chA[CurWpt:]+chA[:CurWpt]
        chB = chB[CurWpt:]+chB[:CurWpt]



        TrgPosition = TrgWpt-CurWpt
        if TrgPosition<0:
            TrgPosition += 2**14

        ii  = np.arange(len(chA)) - TrgPosition
        tt  = ii*TICK*data['Dec']

        if raw:
            chA = np.array(chA,dtype=np.int16)
            chB = np.array(chB,dtype=np.int16)
        else:
            chA = self._to_volts(chA, data, 'A')
            chB = self._to_volts(chB, data, 'B')

        return tt , chA , chB


    def measure(self,trig_channel, dec=1, trig_pos=0,  threshold=0 , hysteresis=63, average=None , wait=False, timeout=10):
        """
        Prepares de Oscilloscope for triggered measurement
            - trig_channel is the number or name of the trigger channel
              Should be 1 to 7 or one of these:
                 'manual','A_rising','A_falling','B_rising','B_falling','ext_rising','ext_falling'
              ('ext' is the trigger made by the lock module: see lock.trig_sw)
            - trig_pos position of the trigger on the final adquisition
                can be a float between 0 and 1 or an int between 0 and 16383 (samples before the trigger)
            - dec is decimation: 1 to 1048575 (the web interface uses up to 524288)
                Sample rate will be: 1/(dec*8 ns)
            - threshold: trigger level. Default is 0
            - hysteresis: to avoid noise trigger. Default is 63 int
            - average: True/False sets the average inside the decimation period (AvgEn).
                       None (default) leaves it as it is.
            - wait: if True, waits until the acquisition is finished (timeout in seconds)

        Sequence (as the C controller): reset, configuration, arm, wait for the pre-trigger samples,
        trigger unlock (2.0 scope), trigger source. Read the result with curv() or dump().

        WARNING: stop the scope of the web page first (make a Single acquisition): both use the scope.
        """

        if type(trig_channel) == str:
            TrgSrc=-1
            try:
                TrgSrc = self.trigger_values.index(trig_channel)
            except ValueError:
                for jj,val in enumerate(self.trigger_values):
                    if jj>0 and trig_channel == val[:len(trig_channel)]:
                        TrgSrc=jj
                        break
            if TrgSrc<1:
                raise ValueError('Trigger channel should be one of this: ' + ','.join(self.trigger_values[1:]))
        else:
            TrgSrc = _to_int(trig_channel)
            if TrgSrc<1 or TrgSrc>7:
                raise ValueError('Trigger channel should be 1 to 7 or one of this: ' + ','.join(self.trigger_values[1:]))

        dec = _to_int(dec)
        dec_max = self._registers.get('Dec', [5,0,0,0,1048575])[4]
        if dec<1 or dec>dec_max:
            raise ValueError(f'dec should be between 1 and {dec_max}')

        if type(trig_pos) == float and trig_pos>=0 and trig_pos<=1:
            trig_pos = int(round( trig_pos* (16383) ))
        else:
            trig_pos = _to_int(trig_pos)
            if trig_pos<0 or trig_pos>16383:
                raise ValueError('trig_pos shoult be between 0 and 16383')

        params = {}
        if TrgSrc in (2,3):
            params['ChAth']  = _to_int(threshold)
            params['ChAHys'] = _to_int(hysteresis)
        if TrgSrc in (4,5):
            params['ChBth']  = _to_int(threshold)
            params['ChBHys'] = _to_int(hysteresis)

        params['Dec']       = dec
        params['TrgDelay']  = 16384-trig_pos  # acquisitions after trigger
        if average is not None:
            params['AvgEn'] = int(bool(average))

        self.set('conf', self.CONF_RST)                     # reset of the write state machine
        self.set(params)                                    # configuration (order does not matter)
        self.set('conf', self.CONF_ARM)                     # arm
        sleep(trig_pos*TICK*dec*1.2 + 0.001)                # pre-trigger samples
        self.unlock_trigger()                               # 2.0: re-enable the trigger (before the source)
        self.set('TrgSrc', TrgSrc)                          # trigger source

        self._last_measure = dict(Dec=dec, TrgDelay=params['TrgDelay'], TrgSrc=TrgSrc)

        if wait:
            self.wait(timeout=timeout)
            self.check_not_overwritten()

        return True

    def check_not_overwritten(self):
        """
        Warns if Dec / TrgDelay are not the ones written by the last measure(): the scope of the web page
        (C controller) is acquiring at the same time and the data may be its own acquisition.
        """
        last = getattr(self, '_last_measure', None)
        if last is None:
            return True
        now = self.get(['Dec','TrgDelay'])
        if now.get('Dec') != last['Dec'] or now.get('TrgDelay') != last['TrgDelay']:
            warnings.warn('The scope registers changed after measure(): the web page is acquiring '
                          '(stop it with a Single acquisition).')
            return False
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
                {rp}.acquire()                           : measure + wait + curv in one call
                {rp}.save_last_meas()                    : Save last acquired data
                {rp}.wait_osc_finish()                   : wait until acquisition is finished
                {rp}.plot_meas()                         : Fast plot of last acquisition

                {rp}.set_signal() / set_gain()           : Lock-in input and gains
                {rp}.set_freq() / set_freq_hz()          : Modulation frequency
                {rp}.set_phase()                         : Phase of cos_1f..3f
                {rp}.set_modulation_amplitud()           : Modulation added to OUT1/OUT2
                {rp}.set_lpf()                           : Configure Low Pass Filters values
                {rp}.get_lpf()                           : Show Low Pass Filters values in human readble format
                {rp}.get_XY()                            : Get demodulated values from lock-in module

                {rp}.set_pid() / get_pid() / pid_reset() : PID A and PID B
                {rp}.set_ramp() / get_ramp()             : Ramp (scan)
                {rp}.set_manual()                        : Manual enables of ramp / PIDs (lock_control)
                {rp}.lock_config() / lock_launch() / lock_now() / lock_release() / lock_status() / wait_locked()

            """
        self.__doc__ = self.__doc__.replace('{rp}',self.name )

    def __repr__(self):
        return f'RedPitayaApp({self.name})'

    def _get_calib(self):
        """
        Internal function to load calibration values (output of 'calib -rv' on the board).
        Only 'NAME = integer' lines are kept. If the names used by curv(raw=False) / get_XY()
        (FE_CH1_FS_G_HI, FE_CH1_DC_offs, ...) are not there, 8192 counts = 1 V is used.
        """
        self.calib = {}
        try:
            res = requests.get(f'{self.url}/calib', {}, timeout=HTTP_TIMEOUT).text.strip()
        except requests.RequestException:
            return
        for dd in res.split('\n'):
            if '=' not in dd:
                continue
            k, v = dd.split('=', 1)
            try:
                self.calib[k.strip()] = int(v.strip(), 0)
            except ValueError:
                pass


    def streaming_prepare(self):
        """
        Prepares RP for streaming
        """
        res = requests.get(f'{self.url}/streaming',{}, timeout=HTTP_TIMEOUT)
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
            filename = f'{now}_{self.name}_params.npy'.replace(':','_')   # 'host:port' is not valid on Windows


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
        Loads saved params from filename (only the read/write registers; TrgUnlock is skipped)
        """
        if filename is None:
            filename = self.filename

        if filename is None or not os.path.isfile(filename):
            raise ValueError(f'Filename {filename} does not exist')

        data = np.load( filename ,allow_pickle=True ).tolist()

        for key, val in data['lock_values'].items():
            if key in self.lock._registers.keys() and not self.lock._registers[key][2]:
                self.lock.set(key,val)

        for key, val in data['osc_values'].items():
            if key in self.osc._registers.keys() and not self.osc._registers[key][2] and key != 'TrgUnlock':
                self.osc.set(key,val)


    # ---- Oscilloscope ------------------------------------------------------------------------------

    def acquire(self, trig_channel='manual', dec=1, trig_pos=0.5, threshold=0, hysteresis=63,
                average=None, timeout=10, raw=False):
        """
        Acquires both scope channels and returns tt, ch1, ch2 (curv()).
        Arguments as osc.measure(); raw=False returns Volts. The data stays in the last dump
        (save_last_meas(), plot_meas()).
        """
        self.osc.measure(trig_channel, dec=dec, trig_pos=trig_pos, threshold=threshold,
                         hysteresis=hysteresis, average=average, wait=True, timeout=timeout)
        return self.osc.curv(raw=raw)


    # ---- Lock-in -----------------------------------------------------------------------------------

    _lpf_lines = {'ref': 0, 'x': 0, 'y': 0, 'xy': 0, 'f0': 0, 'f1': 1, 'f2': 2, 'f3': 3}

    def _lpf_line_list(self, line):
        if isinstance(line, (list, tuple)):
            return sorted(set( jj for ll in line for jj in self._lpf_line_list(ll) ))
        if isinstance(line, str):
            if line.lower() == 'all':
                return [0, 1, 2, 3]
            if line.lower() in self._lpf_lines:
                return [ self._lpf_lines[line.lower()] ]
        elif isinstance(line, (int, np.integer)) and 0 <= line <= 3:
            return [ int(line) ]
        raise ValueError("line should be 'ref' (or 0: X and Y), 1, 2, 3 ('F1', 'F2', 'F3'), 'all' or a list of them")

    def set_lpf(self, tau_exponent=14, order=2 , line='ref' ):
        """
        Configure Lof Pass Filters
            tau_exponent : The characteristic time will be set to 2**tau_exponent * 8 ns. tau_exponent should be between 14 and 29
            order        : order of the filter. Could be 0 (OFF), 1 or 2
            line         : which line of demodulation will be modified. 'ref' or 0 refers to X and Y lines. 1,2,3 refers to F1, F2, F3 lines.
                           'all' sets the four lines; a list of lines is also accepted.
        Register lpf_F<n> = order << 4 | (tau_exponent - 14)   (lock.v, LP_filter3.v)
        Returns the time constant in seconds.
        """
        tau_exponent = _to_int(tau_exponent)
        order        = _to_int(order)
        if tau_exponent>29 or tau_exponent<14:
            raise ValueError(f'tau_exponent shold be between 14 and 29')
        if order>2 or order<0:
            raise ValueError(f'order should be between 0 (OFF) and 2')

        val  = tau_exponent -14
        val += 16*order

        lines = self._lpf_line_list(line)
        self.lock.set({ f'lpf_F{ll}' : val for ll in lines })

        tau = TICK*2**tau_exponent
        print(f'LPF {",".join("ref" if ll==0 else f"F{ll}" for ll in lines)} was set to 8 ns * 2**{tau_exponent} = {tau*1e6:.0f} us , order {order}')
        return tau

    @staticmethod
    def _lpf_decode(lpf):
        """lpf_F<n> register -> (tau in seconds, order). [5:4] = 3 is order 1 (only filter A)."""
        val   = (lpf & 15) + 14
        order = {0: 0, 1: 1, 2: 2, 3: 1}[(lpf >> 4) & 3]
        return TICK*2**val, order

    def get_lpf(self,line=None):
        """
        Shows Lof Pass Filters in Human readable format
            line: which line of demodulation will be shown. 'ref' or 0 refers to X and Y lines. 1,2,3 refers to F1, F2, F3 lines.
                  With line=None prints the four of them and returns a dict name -> (tau [s], order).
                  With a line returns (tau [s], order).
        """
        regs = self.lock.get(['lpf_F0','lpf_F1','lpf_F2','lpf_F3'])
        lpfs = [ regs[f'lpf_F{jj}'] for jj in range(4) ]

        if line is None:
            print('Values of Low Pass Filters in Human readable numbers (order 0 is OFF):')
            rta = {}
            for lpf,name in zip(lpfs, 'ref F1 F2 F3'.split()):
                tau, order = self._lpf_decode(lpf)
                val = (lpf & 15) + 14
                print(f'{name:4s}: is set to 2**{val:<2d} * 8 ns = {tau} seg , order={order} ')
                rta[name] = (tau, order)
            return rta
        else:
            return self._lpf_decode( lpfs[ self._lpf_line_list(line)[0] ] )

    def get_XY(self,units='V',F=False):
        """
        Get values of lock-in registers.
            units  :  'V' is Volts. Anything else is 'int' values.
            F      : if False, returs X and Y . If True, returns X, Y, F1, F2, F3
        X (in phase, from cos_ref) and Y (quadrature, from sin_ref) are read at the same instant
        (read_ctrl[0] freezes the copies).
        """
        offset = 0
        gain   = 1.0/2**13/2**11

        if units.lower()[0]=='v':
            input_signal = self.lock.signal_sw
            if input_signal in [0,1]:
                calib = self.calib or {}
                if f'FE_CH{input_signal+1}_FS_G_HI' in calib:
                    gain   = calib[f'FE_CH{input_signal+1}_FS_G_HI']*100/2**45/2**11
        else:
            gain = 1.0/2**11

        names = ['X_28','Y_28'] + (['F1_28','F2_28','F3_28'] if F else [])

        read_ctrl           = self.lock.read_ctrl
        self.lock.read_ctrl = read_ctrl | 1
        try:
            vals = self.lock.get(names)
        finally:
            self.lock.read_ctrl = read_ctrl

        return np.array([ (offset+vals[nn])*gain for nn in names ])

    def get_freq(self):
        """
        Returns the lock-in base modulation frequency in Hz
        """
        return 1.0/(  (self.lock.gen_mod_hp+1)*2520*TICK  )

    def get_period(self):
        """
        Returns the lock-in base modulation period in sec
        """
        return (self.lock.gen_mod_hp+1)*2520*TICK

    def set_freq(self, val ):
        """
        Sets the frequency value by setting the 'val' value (in ints) to the lock.gen_mod_hp register.
        Returns the frequency set in Hz

            val  : integer to assign to gen_mod_hp. Can be between 0 to 16383
                   f = 125 MHz / (2520 * (val + 1)) : 49.603 kHz .. 3.03 Hz
        """
        val = _to_int(val)
        if val<0 or val>16383:
            raise ValueError(f'val wrong value. Values should be from 0 to 16383. You tryed to set: {val}')
        self.lock.gen_mod_hp = val
        return self.get_freq()

    def set_freq_hz(self, freq):
        """
        Sets the modulation frequency closest to freq [Hz] (3.03 Hz .. 49.603 kHz).
        Returns the frequency set in Hz.
        """
        hp = int(round( 1.0/(freq*2520*TICK) )) - 1
        return self.set_freq( min(16383, max(0, hp)) )


    def set_modulation_amplitud(self,val,ch='out1'):
        """
        Sets the amplitude of modulation over an specific output channel. It's equivalent
        to setting the lock.mod_out[1,2] register to that value.
        Returns the modulation amplitude in Volts.
            val  : integer from -1 to 8191 . -1 means OFF. 0 is 0 Volts amplitude. 8192 ints equals to 1 Volt.
            ch   : channel. Can be 'out1' or 'out2'
        """
        val = _to_int(val)
        if val<-1 or val>8191:
            raise ValueError(f'val wrong value. Values should be from -1 to 8191. You tryed to set: {val}')

        if not ch.lower() in ['out1','out2']:
            raise ValueError(f"ch wrong value. Should be 'out1' or 'out2'. You set: {ch}")

        setattr(self.lock, 'mod_out'+ch[-1] , val )

        return float(val)/8192/2


    def set_phase(self,val):
        """
        Sets the phase value by setting the 'val' value (in ints) to the lock.gen_mod_phase register.
        The value representa the de-phasing of cos_ref vs cos_1f (and also cos_2f and cos_3f).
        Returns the phase in degrees

            val  : integer to assign to gen_mod_phase. Can be between 0 to 2519. 2520 represents 360°
        """
        val = _to_int(val)
        if val<0 or val>2519:
            raise ValueError(f'val wrong value. Values should be from 0 to 2519. You tryed to set: {val}')

        self.lock.gen_mod_phase = val

        return float(val)/2520*360

    def set_signal(self, sw):
        """
        Selects the input of the lock-in (signal_sw): 0 'in1', 1 'in2', 2 'in1-in2', 3 'cos_ref',
        4 'sin_ref', 5 'cos_1f', 6 'aux_A', 7 'Ramp A' (number or label).
        Returns the label set.
        """
        val = self.lock.set('signal_sw', sw)
        return reg_labels['signal_sw'].get(val, val)

    def set_gain(self, line, amp):
        """
        Gain of the demodulated outputs (sg_amp0..3): Xo, Yo = X, Y * 2**sg_amp0, Fno = Fn * 2**sg_ampn
            line : 'ref' (or 0: Xo and Yo), 1, 2, 3 ('F1', 'F2', 'F3')
            amp  : exponent (0..19 for ref, 0..9 for F1..F3) or label ('x1', 'x32', 'x1k', ...)
        Returns the gain factor.
        """
        ll  = self._lpf_line_list(line)[0]
        val = self.lock.set(f'sg_amp{ll}', amp)
        return 2**val


    # ---- PID ---------------------------------------------------------------------------------------

    _pid_regs = ['sw','PSR','ISR','DSR','SAT','sp','kp','ki','kd','ctrl']

    @staticmethod
    def _pid_name(pid):
        pid = str(pid).upper().replace('PID','').strip()
        if pid not in ('A','B'):
            raise ValueError("pid should be 'A' or 'B'")
        return pid

    def set_pid(self, pid='A', sw=None, sp=None, kp=None, ki=None, kd=None,
                PSR=None, ISR=None, DSR=None, SAT=None, ctrl=None):
        """
        Configures PID A or PID B. Only the arguments given are written.
            sw   : input (number or label: 'error','Xo','Yo','F1o','F2o','F3o','signal_i','Ramp A','in1-in2',
                   'in1','in2','aux_A','aux_B','cos_ref','sin_ref','0')
            sp   : set point (counts, -8192..8191; 8192 = 1 V)
            kp, ki, kd : gains (-8192..8191). kp is divided by PSR, the integrator time is
                   8 ns * 2**n(ISR) / ki, the derivative averages 2**n(DSR) samples
            PSR  : 0..4 or '/1','/8','/64','/1024','/4096'
            ISR  : 0..9 or '8 ns','64 ns','512 ns','8 us','65 us','524 us','8 ms','67 ms','537 ms','9 s'
            DSR  : 0..5
            SAT  : saturation of the integral term, 0..13 (±2**SAT counts, 13 = ±1 V)
            ctrl : [0] integrator reset, [1] freeze output, [2] freeze integrator
        The PID only acts when it is enabled (set_manual() / lock_config(), lock_status()).
        Returns get_pid(pid).
        """
        pid  = self._pid_name(pid)
        args = dict(sw=sw, PSR=PSR, ISR=ISR, DSR=DSR, SAT=SAT, sp=sp, kp=kp, ki=ki, kd=kd, ctrl=ctrl)
        regs = { f'pid{pid}_{k}': v for k,v in args.items() if v is not None }
        if regs:
            self.lock.set(regs)
        return self.get_pid(pid)

    def get_pid(self, pid='A'):
        """
        Registers of PID A or B (without the 'pidX_' prefix) plus 'in', 'out' and the effective
        enable ('enabled', from lock_status).
        """
        pid  = self._pid_name(pid)
        names= [ f'pid{pid}_{k}' for k in self._pid_regs+['in','out'] ] + ['lock_status']
        regs = self.lock.get(names)
        rta  = { k.split('_',1)[1]: v for k,v in regs.items() if k.startswith(f'pid{pid}_') }
        rta['enabled'] = bool(regs['lock_status'] & (8 if pid=='A' else 4))
        return rta

    def pid_reset(self, pid='A'):
        """Resets the integrator of PID A or B (pulse of pidX_ctrl bit 0)"""
        pid  = self._pid_name(pid)
        ctrl = self.lock.get(f'pid{pid}_ctrl')
        self.lock.set(f'pid{pid}_ctrl', ctrl | 1)
        self.lock.set(f'pid{pid}_ctrl', ctrl & ~1)


    # ---- Ramp (scan) -------------------------------------------------------------------------------

    _ramp_regs = ['step','low_lim','hig_lim','enable','reset','direction','sawtooth','B_factor']

    def set_ramp(self, step=None, low=None, high=None, enable=None, sawtooth=None, direction=None,
                 B_factor=None, reset=None):
        """
        Configures the ramp generator (scan). Only the arguments given are written.
            step      : each value of the ramp lasts step + 1 ticks of 8 ns (ramp_step, 32 bits)
            low, high : limits (counts, -8192..8191; ramp_low_lim / ramp_hig_lim)
            enable    : ramp_enable (the ramp runs only if this AND the effective ramp enable of the
                        lock control are on: see set_manual(ramp=True) and lock_status())
            sawtooth  : True sawtooth, False triangle
            direction : starting direction (triangle) / direction (sawtooth)
            B_factor  : ramp_B = ramp_A * B_factor / 4096 (-4096..4096)
            reset     : True holds the ramp at 0
        Returns get_ramp().
        """
        args = dict(step=step, low_lim=low, hig_lim=high, enable=enable, sawtooth=sawtooth,
                    direction=direction, B_factor=B_factor, reset=reset)
        regs = { f'ramp_{k}': (int(bool(v)) if k in ('enable','sawtooth','direction','reset') else v)
                 for k,v in args.items() if v is not None }
        if regs:
            self.lock.set(regs)
        return self.get_ramp()

    def get_ramp(self):
        """Ramp registers (without the 'ramp_' prefix) plus the outputs A and B"""
        regs = self.lock.get([ f'ramp_{k}' for k in self._ramp_regs+['A','B'] ])
        return { k.split('_',1)[1]: v for k,v in regs.items() }


    # ---- Lock control (v2.3.13: lock_control = command + configuration, lock_status read only) ----

    _lock_bits = {'pidB': 0, 'pidA': 1, 'ramp': 2}
    _trig_types = {'off': 0, 'time': 1, 'level': 2, 'level_time': 3, 'level+time': 3}

    def lock_status(self):
        """
        Decoded lock_status (0x1C): armed, locked, effective enables (ramp, pidA, pidB) and the
        number of entries into LOCKED (modulo 256).
        """
        s = self.lock.lock_status
        return dict(armed=bool(s & 1), locked=bool(s >> 1 & 1), pidB=bool(s >> 2 & 1),
                    pidA=bool(s >> 3 & 1), ramp=bool(s >> 4 & 1), count=(s >> 8) & 0xff, raw=s)

    def get_lock_control(self):
        """Decoded lock_control (0x18)"""
        v = self.lock.lock_control
        tt = {v_: k for k,v_ in self._trig_types.items()}
        return dict(lock_now=bool(v & 1), launch_lock=bool(v & 2),
                    manual=[ k for k,b in self._lock_bits.items() if v >> (2+b) & 1 ],
                    final =[ k for k,b in self._lock_bits.items() if v >> (5+b) & 1 ],
                    trig_type=tt[(v >> 8) & 3], rise=bool(v >> 10 & 1), raw=v)

    def _enables(self, names):
        if isinstance(names, str):
            names = [ n for n in names.replace(',',' ').split() ]
        bits = 0
        for n in names:
            if n not in self._lock_bits:
                raise ValueError(f"enable names should be 'ramp', 'pidA', 'pidB'. Got: {n}")
            bits |= 1 << self._lock_bits[n]
        return bits

    def set_manual(self, ramp=None, pidA=None, pidB=None):
        """
        Manual enables (lock_control bits 4:2): the enables of the ramp and the PIDs while not LOCKED
        ("Scan enable" / "PID A" / "PID B" buttons of the page). Only the arguments given change.
        Changing one of them while LOCKED releases the lock (manual override).
        Returns lock_status().
        """
        v = self.lock.lock_control
        for name, on in (('ramp', ramp), ('pidA', pidA), ('pidB', pidB)):
            if on is not None:
                bit = 1 << (2 + self._lock_bits[name])
                v = (v | bit) if on else (v & ~bit)
        self.lock.lock_control = v
        return self.lock_status()

    def lock_config(self, trig='time', time=None, time_ticks=None, level=None, level_V=None,
                    signal=None, rise=True, final=('pidA',), manual=None):
        """
        Configures the lock (auto-lock) without requesting it. Writes lock_control with the request
        bits [1:0] = 00, so AN ACTIVE LOCK IS RELEASED (same as py/lock_from_registers.py).
            trig       : 'time' (time after the scan floor), 'level' (signal crossing a level),
                         'level_time' (level crossing after the time) or 'off' (only lock_now())
            time       : time trigger in seconds after the scan floor (or time_ticks, ticks of 8 ns,
                         0 .. 2**32-1 = 34.4 s with the FPGA of v2.3.15)
            level      : level in counts (-8192..8191) or level_V in Volts (8192 counts = 1 V)
            signal     : signal of the level trigger (lock_trig_sw, number or label: 'error','Xo',
                         'Yo','F1o','F2o','F3o','signal_i','Ramp A','aux_A','in1','in2','in1-in2','PID A out')
            rise       : level crossing upwards (True) or downwards (False)
            final      : enables while LOCKED, e.g. ('pidA',) or ('pidA','pidB') or 'pidA,pidB'
            manual     : enables while not locked; None keeps the current ones (usually ('ramp',))
        Returns the value written to lock_control.
        """
        if trig not in self._trig_types:
            raise ValueError("trig should be 'time', 'level', 'level_time' or 'off'")
        regs = {}
        if time is not None:
            time_ticks = int(round(time / TICK))
        if time_ticks is not None:
            time_ticks = _to_int(time_ticks)
            if time_ticks < 0 or time_ticks > 2**32-1:
                raise ValueError('time should be between 0 and 34.36 s (2**32-1 ticks of 8 ns)')
            regs['lock_trig_time'] = time_ticks
        if level_V is not None:
            level = int(round(level_V*8192))
        if level is not None:
            level = _to_int(level)
            if level < -8192 or level > 8191:
                raise ValueError('level should be between -8192 and 8191 counts (-1 V .. 1 V)')
            regs['lock_trig_val'] = level
        if signal is not None:
            regs['lock_trig_sw'] = self.lock._value('lock_trig_sw', signal)
        if regs:
            self.lock.set(regs)

        old = self.lock.lock_control
        man = ((old >> 2) & 7) if manual is None else self._enables(manual)
        v   = (man << 2) | (self._enables(final) << 5) | (self._trig_types[trig] << 8) | (int(bool(rise)) << 10)
        self.lock.lock_control = v
        return v

    def _lock_request(self, bit, timeout):
        v = self.lock.lock_control & ~3
        self.lock.lock_control = v            # [1:0] = 00 first: the FPGA acts on the 0->1 edge
        self.lock.lock_control = v | bit
        if timeout:
            return self.wait_locked(timeout=timeout)
        return self.lock_status()

    def lock_launch(self, timeout=None):
        """
        Trigger Lock: arms the lock (lock_control bit 1, 0->1 edge); the trigger configured with
        lock_config() locks. With timeout (s) waits for LOCKED (wait_locked()).
        Returns lock_status().
        """
        return self._lock_request(2, timeout)

    def lock_now(self):
        """Lock Now: locks immediately (lock_control bit 0, 0->1 edge). Returns lock_status()."""
        return self._lock_request(1, None)

    def lock_release(self):
        """Releases the lock (lock_control [1:0] = 00): back to the manual enables. Returns lock_status()."""
        self.lock.lock_control = self.lock.lock_control & ~3
        return self.lock_status()

    def wait_locked(self, timeout=10, poll=0.01):
        """Waits for the state LOCKED. Returns lock_status() or raises AcquisitionTimeout."""
        t0 = time()
        while True:
            st = self.lock_status()
            if st['locked']:
                return st
            if time()-t0 > timeout:
                raise AcquisitionTimeout(f'Not locked after {timeout} sec: {st}')
            sleep(poll)


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
        self.osc.wait(timeout=timeout, poll=0.1, verbose=True)
        return 0

    def plot_meas(self, filename=None , raw=False ):
        """
        Fast plot of acquisition.
            filename : if None, plot last acquisition. If filename path, plot saved data.
            raw      : if True, use int instead of Volts as units.
        """
        if filename is None:
            data = self._last_osc_dump
            if self.filename is None and 'lock_values' not in data:
                data['lock_values'] = self.lock.get(['oscA_sw','oscB_sw'])
        elif os.path.isfile(filename):
            saved = np.load( filename ,allow_pickle=True ).tolist()
            data  = saved['dump']
            if 'lock_values' in saved and 'lock_values' not in data:
                data['lock_values'] = saved['lock_values']
        else:
            raise ValueError(f'Filename {filename} does not exist')

        tt, ch1, ch2 = self.osc.curv( data=data , raw=raw )

        from matplotlib import pyplot as plt

        fig, ax = plt.subplots( 2,1, figsize=(13,7) ,  constrained_layout=True , sharex=True )

        ax[0].plot( tt, ch1 )
        ax[1].plot( tt, ch2 )
        ax[1].set_xlabel('time [sec]')

        label1 = label2 = ''
        sw = dict(data.get('lock_values', {}))
        sw.update({ k: data[k] for k in ('oscA_sw','oscB_sw') if k in data })
        if 'oscA_sw' in sw:
            label1 = reg_labels['oscA_sw'].get( sw['oscA_sw'], '' ) + ' '
        if 'oscB_sw' in sw:
            label2 = reg_labels['oscB_sw'].get( sw['oscB_sw'], '' ) + ' '

        units = 'int' if raw else 'V'
        ax[0].set_ylabel(f'ch1 {label1}[{units}]')
        ax[1].set_ylabel(f'ch2 {label2}[{units}]')

        for aa in ax:
            aa.grid(True,linestyle= '--',color='lightgray')

        return fig, ax


# rp = RedPitayaApp('med00.npy')





# rp = RedPitayaApp('http://rp-f00a3b.local/lock_in+pid_harmonic/?type=run')


# rp.save_params('med00.npy')



#rp.osc.measure('ext', dec=1 , trig_pos=8191 )

#rp.osc.dump()


# rp.plot_meas()

#    rp.osc.measure('B_ri', dec=1024 , trig_pos=8191 , hysteresis=1, threshold=5000)

#
#
#    while not rp.osc.acq_done():
#        sleep(0.1)

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
