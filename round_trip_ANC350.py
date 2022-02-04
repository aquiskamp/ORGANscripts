# round trip time for ANC350 positioners
__author__ = 'Aaron'

import time
from attocube.ANC350 import Positioner

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']

ax = {'x':0,'y':1}
anc = Positioner()

print('Connected to',anc.getActuatorName(ax['y']))
print('Current Position',anc.getPosition(ax['y']))

setVoltage = {'y': 60} # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'y': 1000} # freq in
anc.setAmplitude(ax['y'],setVoltage['y']) #This sets the voltage for the sweep.
anc.setFrequency(ax['y'],setFreq['y']) #This sets the frequency for the sweep.
direction =  0 #If the move direction is forward (0) or backward (1)

#move to start
start_pos = anc.getPosition(ax['y'])
anc.setTargetPosition(ax['y'],360)
anc.setTargetRange(ax['y'], 1e-3)  # set precision
anc.setAxisOutput(ax['y'], 1, 1)  # set output to axis, (1) enable (0) disable, autodisable when stop (1)
print('Starting at %s degrees'%start_pos)
start_time = time.time()
anc.startAutoMove(ax['y'],1,1)
rt_time = time.time() - start_time
print('Round trip time: %s seconds'%rt_time)
