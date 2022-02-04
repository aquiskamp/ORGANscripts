__author__ = 'Aaron'
#adapt script to use closed loop positioner and ANC35 controller

import warnings
import time
import numpy as np
import cryolib.general as gen
import matplotlib
import matplotlib.pyplot as plt
from prettytable import PrettyTable
import vna_single_sweep as vnass
import lakeshore_temp as lakesm
from pathlib import Path as p
from attocube.attocube import ANC300
from datetime import datetime
from pytz import timezone
import h5py
from tqdm import tqdm
from attocube.ato_func import ato_hdf5_parser
from matplotlib import cm
from matplotlib.colors import Normalize
from matplotlib.backends.backend_pdf import PdfPages
from attocube.ANC350 import Positioner
# Folder To Save Files to:
exp_name = 'Warmup_4K_run_1'
filepath = p.home()/'Desktop'/'ORGAN_15GHz'/'Bevel_Rod'/exp_name

measure_cap = False
cap = 0
time_interval = 2*60 #seconds

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']

ax = {'x':0,'y':1}
anc350 = Positioner()
anc = ANC300()
up_down = 'd' # set to up, to set to down replace 'u' with 'd'

setVoltage = {'x': 60} # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'x': 1000} # freq in

anc.V = setVoltage #This sets the voltage for the sweep.
anc.freq = setFreq #This sets the frequency for the sweep.

n_steps = 500 #n single steps
step_size = 500
ato_pos_vals = np.arange(0,step_size*(n_steps+1),step_size)

initial_position = anc350.getPosition(ax['y'])
print('Connected to',anc350.getActuatorName(ax['y']))
print('Current Position',initial_position)
phi_array = np.array([])
time.sleep(1000)
for idx,ato_pos in enumerate(tqdm(ato_pos_vals)):
    print("Moving to ato_pos: %s (steps)" % (ato_pos))
    if ato_pos == 0 or idx == 0: #since send a 0 instructs the stage to move continuously
        anc.stop()
        anc.ground()
    else:
        anc.step('x', step_size, up_down)
    time.sleep(0.1)
    pos_after_step = anc350.getPosition(ax['y'])

    if measure_cap:
        cap = anc.cap['x']
    t = datetime.now(timezone('Australia/Perth')).strftime(fmt)

    with h5py.File(filepath/p(exp_name + '.hdf5'), 'a') as f:
        try:
            if f[str(ato_pos)]:
                del(f[str(ato_pos)])
        except:
            None
        dset = f.create_dataset(str(ato_pos), data = [], compression='gzip', compression_opts=9)
        dset.attrs['ato_pos'] = ato_pos
        dset.attrs['phi_deg'] = pos_after_step
        dset.attrs['time'] = t
        dset.attrs['cap'] = cap

    print('Current Stage position:%s. Starting position:%s'%(pos_after_step,initial_position))
    time.sleep(time_interval)
    # phi_array = np.append(phi_array,pos_after_step)
    # time_step = np.arange(phi_array.size)
    # plt.plot(time_step,phi_array)
    # plt.xlabel('Time (steps)')
    # plt.ylabel('phi (deg)')