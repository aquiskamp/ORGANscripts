import time
import numpy as np

from attocube.ANC350 import Positioner
ax = {'x':0,'y':1}
anc = Positioner()

print('Connected to',anc.getActuatorName(ax['x']))
print('Current Position',anc.getPosition(ax['x']))

setVoltage = {'x': 60} # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'x': 500} # freq in
anc.setAmplitude(ax['x'],setVoltage['x']) #This sets the voltage for the sweep.
anc.setFrequency(ax['x'],setFreq['x']) #This sets the frequency for the sweep.
anc.setAxisOutput(ax['x'], 1, 0)  # set output to axis, (1) enable (0) disable, autodisable when stop (1)
anc.setTargetPosition(ax['x'], 1e-5)  # set axis, set degrees
anc.setTargetRange(ax['x'], 1e-6)  # set precision

#move to start
while True:
    anc.startAutoMove(ax['x'], 1, 1)  # axis, enable/disable, absolute (0) or relative to the current position (1)
    print('Current Position', anc.getPosition(ax['x']))
    time.sleep(30)