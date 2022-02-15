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
        self.host = 'COM3' #usb address

    def connect(self):
            rm = pyvisa.ResourceManager()
            self.inst = rm.open_resource(self.host)
            self.connected = True 

    def close(self):
        '''
        Closes connection
        '''
        self.inst.close()

    def freq(self, f):
        for key, value in f.items():
            self.send('setf %i %i' %(self._stages.index(key)+1, value)) # e.g. setf 1 100 to set x axis to 100 Hz

    def mode(self, m):
        """ Mode, choose from: gnd, cap, stp """
        for key, value in m.items():
                self.send('setm %i %s' %(self._stages.index(key)+1, value))

    def V(self, v):
        for key, value in v.items():
            self.send('setv %i %i' %(self._stages.index(key)+1, value)) # e.g. setf 1 10 to set x axis to 10 V

    def cap(self):
        self.mode = {'x':'cap'}
        for i in range(1):
            self.send('capw %i' %(i+1)) # wait for capacitance measurement to finish
            msg = self.send('getc %i' %(i+1))
        return msg

    def ground(self):
        self.mode = {'x':'gnd'}

    def step(self, axis, numsteps, updown):
        """ steps up for number of steps given; if None, ignored; if 0, continuous"""

        if updown not in ['u','d']:
            raise Exception('What doesn\'t come up must come down!')

        self.mode = {axis: 'stp'}

        if numsteps == 0:
            raise Exception('That won\'t get you anywhere!')
            # msg = self.send('step%s %i c' %(updown, i+1)) NO!!!!! THIS IS BAD!!! WE DON'T WANT TO MOVE CONTINUOUSLY
        else:
            self.send('step%s %i %i' %(updown, self._stages.index(axis)+1, numsteps))
            self.send('stepw %i' %(self._stages.index(axis)+1)) # waits until motion has ended to run next command; Attocube.stop will stop motion no matter what
        self.mode = {axis: 'gnd'}

    def stop(self):
        for i in range(1):
            msg = self.send('stop %i' %(i+1))

    def send(self, cmd):
        self.connect()
        try:
            self.inst.write(cmd)
        except:
            print("Could not connect to ANC300 Attocube Controller!")


