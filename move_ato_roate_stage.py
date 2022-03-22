__author__ = 'Aaron Quiskamp'

import time
import numpy as np
import pyvisa
from tqdm import tqdm
from attocube.attocube_usb import ANC300

wait_time = 1*15 #seconds

up_down = 'u' # set to up, to set to down replace 'u' with 'd'
setVoltage = 5 # key-value pair, x is axis, '60' is voltage Volts
setFreq = 1000 # freq in Hz
rm = pyvisa.ResourceManager()
print(rm.list_resources())
inst = rm.open_resource('COM3') #usually COM3
inst.write('setv 1 3')
# # inst.write('setf 1 1000')
inst.write('setm 1 gnd')
# # inst.write('stepd 1 20000')
# # time.sleep(30)
# inst.read_termination = '\n'
# inst.write('setm 1 cap')
# inst.write('capw 1')
# # #read_termination = '\n'
# inst.read_termination = '\n'
# inst.write('getc 1')
# print(inst.read())
# print(inst.read())
#
# while True:
#     print(inst.read_values())

#anc = ANC300()
#
# setVoltage = {'x': 10} # key-value pair, x is axis, '60' is voltage Volts
# setFreq = {'x': 50} # freq in
#print(anc.cap())
# anc.freq(setFreq)
# anc.V(setVoltage)
# anc.ground()
# print(anc.cap())

