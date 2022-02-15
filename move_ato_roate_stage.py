__author__ = 'Aaron Quiskamp'

import time
import numpy as np
import pyvisa
from tqdm import tqdm
from attocube.attocube_usb import ANC300

wait_time = 1*15 #seconds

up_down = 'u' # set to up, to set to down replace 'u' with 'd'
setVoltage = 60 # key-value pair, x is axis, '60' is voltage Volts
setFreq = 1000 # freq in Hz

# rm = pyvisa.ResourceManager()
# inst = rm.open_resource('COM3') #usually COM3
# inst.write('setv 1 60')
# inst.write('setf 1 1000')
# inst.write('setm 1 stp')
# inst.write('stepd 1 20000')
# time.sleep(30)
# inst.write('setm 1 gnd')


anc = ANC300()

setVoltage = {'x': 60} # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'x': 1000} # freq in

anc.freq = setFreq #This sets the frequency for the sweep.

