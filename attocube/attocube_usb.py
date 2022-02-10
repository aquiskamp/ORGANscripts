import atexit
import time
import telnetlib
import re
import pyvisa
import numpy as np
class ANC300():
    
    _stages = ['x']
    _modes = ['gnd','cap','stp']
    
    def __init__(self):
        
        self.tn = None
        self.host = 'COM3' #usb address
        self._freq = {}
        self._mode = {}
        self._V = {}
        self._cap = {}

        self.freq
        self.mode
        self.V

    def connect(self):
            rm = pyvisa.ResourceManager()
            self._tn = rm.open_resource(self.host)
            self.connected = True 
           

    def close(self):
        '''
        Closes telnet connection
        '''
        self._tn.close()

    def help(self):
        msg = self.send('help')
        print(msg)

    @property
    def freq(self):
        for i in range(1):
            msg = self.send('getf %i' %(i+1)) # i+1 -> controllers labeled 1,2,3, not 0,1,2
        return msg

    @freq.setter
    def freq(self, f):
        for key, value in f.items():
            self.send('setf %i %i' %(self._stages.index(key)+1, value)) # e.g. setf 1 100 to set x axis to 100 Hz

    @property
    def mode(self):
        """ Mode, choose from: gnd, cap, stp """
        for i in range(1):
            msg = self.send('getm %i' %(i+1)) # i+1 -> controllers labeled 1,2,3, not 0,1,2
        return msg

    @mode.setter
    def mode(self, m):
        for key, value in m.items():
                msg = self.send('setm %i %s' %(self._stages.index(key)+1, value))

    @property
    def V(self):
        for i in range(1):
            msg = self.send('getv %i' %(i+1)) # i+1 -> controllers labeled 1,2,3, not 0,1,2
        return msg

    @V.setter
    def V(self, v):
        for key, value in v.items():
            self.send('setv %i %i' %(self._stages.index(key)+1, value)) # e.g. setf 1 10 to set x axis to 10 V

    @property
    def cap(self):
        self.mode = {'x':'cap'}
        for i in range(1):
            self.send('capw %i' %(i+1)) # wait for capacitance measurement to finish
            msg = self.send('getc %i' %(i+1))
            #self._cap[self._stages[i]] = float(self._getValue(msg))
        return msg

    def close(self):
        '''
        Closes telnet connection
        '''
        self._tn.close()



    def check_voltage(self):
        for key, value in self.V.items():
            if value > self._V_lim:
                self.V = {key: self._V_lim}
                print("Axis %s voltage was too high, set to %f" %(key, self._V_lim))

    def ground(self):
        self.mode = {'x':'gnd'}

    def step(self, axis, numsteps, updown):
        """ steps up for number of steps given; if None, ignored; if 0, continuous"""
        self.check_voltage()

        if updown not in ['u','d']:
            raise Exception('What doesn\'t come up must come down!')

        self.mode = {axis: 'stp'}
        if numsteps > self._step_lim:
            raise Exception('too many steps! Max %i' %self._step_lim)
        elif numsteps == 0:
            raise Exception('That won\'t get you anywhere!')
            # msg = self.send('step%s %i c' %(updown, i+1)) NO!!!!! THIS IS BAD!!! WE DON'T WANT TO MOVE CONTINUOUSLY
        else:
            self.send('step%s %i %i' %(updown, self._stages.index(axis)+1, numsteps))
            self.send('stepw %i' %(self._stages.index(axis)+1)) # waits until motion has ended to run next command; Attocube.stop will stop motion no matter what
        self.mode = {axis: 'gnd'}

    def move(self, numsteps):
        self.up(numsteps)

    def up(self, numsteps):
        for axis, num in numsteps.items():
            if num > 0:
                upordown = 'u'
            else:
                num = -num
                upordown = 'd'
            self.step(axis, num, upordown)

    def down(self, numsteps):
        for axis, num in numsteps.items():
            if num > 0:
                upordown = 'd'
            else:
                num = -num
                upordown = 'u'
            self.step(axis, num, upordown)

    def stop(self):
        for i in range(1):
            msg = self.send('stop %i' %(i+1))

    def send(self, cmd):
        self.connect()
        try:
            self._tn.write(cmd)
        except:
            print("Could not connect to ANC300 Attocube Controller!")



    def _getDigits(self,msg):
        """ Extracts digits from attocube message """
        for s in str(msg).split():
            if s.isdigit():
                return int(s)
        raise Exception('no numbers found') # will only run if number is not returned
        #integ = int(re.search(r'\d+', str(msg)).group())

    def _getValue(self, msg):
        """ Looks after equals sign in returned message to get value of parameter """
        return msg.split()[msg.split().index(b'=')+1].decode('utf-8') #looks after the equal sign
