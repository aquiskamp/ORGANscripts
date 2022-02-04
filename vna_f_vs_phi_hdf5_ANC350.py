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
from datetime import datetime
from pytz import timezone
import h5py
from tqdm import tqdm
from attocube.ato_func import ato_hdf5_parser
from matplotlib import cm
from matplotlib.colors import Normalize
from matplotlib.backends.backend_pdf import PdfPages

# Folder To Save Files to:
exp_name = 'RT_trans_run_1'
filepath = p.home()/'Desktop'/'ORGAN_15GHz'/'70mm_cavity'/exp_name

db_max = -80
db_min = -30

# fcentral, fspan, bandwidth, npoints, naverages, power
runfile = p('run1.csv')

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']
matplotlib.use('TkAgg')

# Static Temperature:
measure_temp = False  # Do we actually want to measure Temperature here (Connect to Lakeshore via GPIB)?
temperature = 20e-3  # (Kelvin) Manual Temperature Record (For No Lakeshore Access)

from attocube.ANC350 import Positioner
ax = {'x':0,'y':1}
anc = Positioner()

print('Connected to',anc.getActuatorName(ax['y']))
print('Current Position',anc.getPosition(ax['y']))

ato_start = 56 #for closed loop control
ato_stop = 120
ato_tune = np.abs(ato_stop - ato_start)
ato_step = 0.4
total_steps = int(ato_tune/ato_step) + 1

setVoltage = {'y': 60} # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'y': 1000} # freq in
anc.setAmplitude(ax['y'],setVoltage['y']) #This sets the voltage for the sweep.
anc.setFrequency(ax['y'],setFreq['y']) #This sets the frequency for the sweep.

#move to start
target = 0
anc.setAxisOutput(ax['y'], 1, 1)  # set output to axis, (1) enable (0) disable, autodisable when stop (1)
anc.setTargetPosition(ax['y'], ato_start)  # set axis, set degrees
anc.setTargetRange(ax['y'], 1e-3)  # set precision
print("Moving to ato_pos: %s degrees" % (ato_start))
anc.startAutoMove(ax['y'], 1, 0)  # axis, enable/disable, absolute (0) or relative to the current position (1)
while target == 0:
    connected, enabled, moving, target, eotFwd, eotBwd, error = anc.getAxisStatus(ax['y'])  # find bitmask of status
    if target == 0:
        None
    elif target == 1:
        print('axis arrived at', anc.getPosition(ax['y']))
        anc.startAutoMove(ax['y'], 0, 0)  # disable axis

# Starting Scan:
ato_pos_vals = np.arange(ato_start,ato_stop + ato_step, ato_step)

# SCRIPT STARTS HERE
# Send error notifications to email addresses:
warn_email_list = ['21727308@student.uwa.edu.au']

# Other Settings:
sweep_type = "phi_pos"

# Additional VNA Settings
channel = "1" #VNA Channel Number
warnings.filterwarnings('ignore', '.*GUI is implemented*') # Suppress Matplotlib warning
plt.ion()
fig = plt.figure("VNA DOWNLOAD")
plt.draw()

plt.ion()
fig1 = plt.figure("MODE MAP")
plt.draw()

mode_list = np.loadtxt(filepath/runfile, dtype='f8,f8,f8,i,i,f8', delimiter=',')
if np.size(mode_list) == 1: # In case we have only one mode
    mode_list = np.asarray([mode_list])

# Plotting mode measurement settings as a nice table:
dat_dtype = {
    'names': ('Fcent (Hz)', 'Fspan (Hz)', 'BW (Hz)', 'NPoints', 'NAverages', 'Power (dBm)'),
    'formats': ('f8', 'f8', 'f8', 'i', 'i', 'f8')}
dat = np.zeros(7, dat_dtype)

table_data = PrettyTable(dat.dtype.names)
for row in mode_list:
    table_data.add_row(row)

print("Loaded Settings:")
print(table_data)

vnass.set_module(channel, warn_email_list) # Reset VNA Module
vnass.establish_connection()    # Establish connection to VNA

# Attocube code begins
anc.setAxisOutput(ax['y'], 1, 1) #set output to axis, (1) enable (0) disable, autodisable when stop (1)
anc.setTargetRange(ax['y'],1e-3) # set precision
target = 0

for idx,ato_pos in enumerate(tqdm(ato_pos_vals)):
    current_pos = anc.getPosition(ax['y'])
    anc.setTargetPosition(ax['y'], ato_pos)  # set axis, set degrees
    print("Moving to ato_pos: %s degrees" % (ato_pos))
    while target == 0:
        connected, enabled, moving, target, eotFwd, eotBwd, error = anc.getAxisStatus(ax['y'])  # find bitmask of status
        if target == 0:
            anc.startAutoMove(ax['y'], 1, 0)  # axis, enable/disable, absolute (0) or relative to the current position (1)
        elif target == 1:
            print('Axis arrived at %s degrees' %anc.getPosition(ax['y']))
            anc.startAutoMove(ax['y'], 0, 0) #disable axis
    target = 0 #reset target
    pos_after_step = anc.getPosition(ax['y'])
# Attocube code ends

    # Sweep over vna modes
    for mode in mode_list:
        sweep_data = vnass.sweep(mode)  # Do a sweep with these parameters

        fcent = mode[0]
        fspan = mode[1]
        bandwidth = mode[2]
        npoints = int(mode[3])
        naverages = mode[4]
        power = mode[5]

        if measure_temp:
            temperature = lakesm.get_temp(LAKE_channel)

        # Processing Starts here
        freq_data = gen.get_frequency_space(fcent, fspan, npoints)  # Generate list of frequencies

        fig.clf()
        ax1 = fig.add_subplot(111)
        ax1.set_title("ato_step_no = %i (%.3f deg), f = %.3f GHz" % (idx, pos_after_step, fcent/1e9), fontsize=16)
        ax1.plot(freq_data/1e9, gen.complex_to_dB(sweep_data), "g")
        ax1.set_ylabel('$S_{21}$ [dB]')
        ax1.set_xlabel('Frequency [GHz]')
        plt.axis('tight')
        plt.draw()

        if list(mode_list).index(mode) == 0:
            ready_data = np.transpose(sweep_data)
        else:
            ready_data = np.vstack((ready_data, np.transpose(sweep_data)[1:]))

        t = datetime.now(timezone('Australia/Perth')).strftime(fmt)

    with h5py.File(filepath/p(exp_name + '.hdf5'), 'a') as f:
        try:
            if f[str(idx)]:
                del(f[str(idx)])
        except:
            None

        full_freq = np.linspace(mode_list[0][0]-fspan//2,fcent + fspan//2,ready_data.shape[0]) #freq list in Hz
        dset = f.create_dataset(str(idx), data = ready_data, compression='gzip', compression_opts=9)  # VNA dset
        try:
            f['Freq']
        except:
            fdset = f.create_dataset('Freq', data=full_freq, compression='gzip', compression_opts=9)
            fdset.attrs['f_start'] = mode_list[0][0]  # this is from the mode map / next freq
            fdset.attrs['f_final'] = fcent
            fdset.attrs['sweep_type'] = sweep_type
            fdset.attrs['vna_pow'] = power
            fdset.attrs['vna_span'] = fspan
            fdset.attrs['vna_pts'] = npoints
            fdset.attrs['vna_ave'] = naverages
            fdset.attrs['vna_rbw'] = fspan/(npoints-1)
            fdset.attrs['vna_ifb'] = bandwidth
            fdset.attrs['nmodes'] = mode_list.shape[0]
            fdset.attrs['ato_voltage'] = setVoltage['y']
            fdset.attrs['ato_freq'] = setFreq['y']
            fdset.attrs['ato_step'] = ato_step
            fdset.attrs['total_steps'] = total_steps
        dset.attrs['ato_pos'] = pos_after_step
        dset.attrs['temp'] = temperature
        dset.attrs['time'] = t
    if idx % 5 == 0 and idx != 0:
        fig1.clf()
        ax2 = fig1.add_subplot(111)
        mag_data_db, freq, phi = ato_hdf5_parser(filepath / p(exp_name + '.hdf5'))
        colour = ax2.imshow(mag_data_db, extent=[phi[0], phi[-1], freq[0], freq[-1]],
                            aspect=(0.8 * (phi[-1] - phi[0]) / (freq[-1] - freq[0])),
                            cmap=plt.cm.get_cmap('viridis'), origin='lower', norm=Normalize(vmin=db_min, vmax=db_max))
        ax2.set_xlabel(r'Phi (Steps)')
        ax2.set_ylabel(r'Frequency (GHz)')
        cb = fig1.colorbar(colour, ax=ax2, fraction=0.0325, pad=0.04)
        cb.set_label('$|S_{21}|$ [dB]')
        cm.ScalarMappable()
        plt.title(exp_name)
        plt.draw()
if measure_temp:
    lakesm.disconnect() # Disconnect from Lakeshore if actively measured temperature

#save modemap
pp = PdfPages(filepath/(exp_name + '_MODE_MAP.pdf'))
fig1.savefig(pp, format='pdf', dpi=600)
pp.close()

print("Closing connection to Stepper Motor ", anc.disconnect())

print("ALL VALUES RECORDED. SWEEP COMPLETE.")
