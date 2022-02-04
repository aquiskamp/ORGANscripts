__author__ = 'Aaron'

import time
import numpy as np
from attocube.attocube import ANC300
from tqdm import tqdm

wait_time = 1*15 #seconds

anc = ANC300()
up_down = 'u' # set to up, to set to down replace 'u' with 'd'

setVoltage = {'x': 60} # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'x': 1000} # freq in

anc.V = setVoltage #This sets the voltage for the sweep.
anc.freq = setFreq #This sets the frequency for the sweep.

ato_pos_end = 8000
step_size = 400
ato_pos_vals = np.arange(step_size,ato_pos_end,step_size)

for idx,ato_pos in enumerate(tqdm(ato_pos_vals)):
    print("Moving to ato_pos: %s (steps)" % (ato_pos))
    if ato_pos == 0: #since send a 0 instructs the stage to move continuously
        anc.stop()
        anc.ground()
    else:
        anc.step('x', step_size, up_down)
    print(f'Sleeping for {wait_time}s')
    time.sleep(wait_time)