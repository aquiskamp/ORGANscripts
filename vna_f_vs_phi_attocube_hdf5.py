__author__ = 'Aaron'
__version__ = '20.03.2015_1.0'

# THIS SCRIPTS INITIATES A frequency vs B-field Sweep Using Agilent VNA and American Magnetics
import warnings
import os
import time
import numpy as np
import cryolib.general as gen
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from prettytable import PrettyTable
from attocube.attocube import ANC300
import vna_single_sweep as vnass
import lakeshore_temp as lakesm
from pathlib import Path as p
from datetime import datetime
from pytz import timezone
import h5py

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']
matplotlib.use('TkAgg')

#New code starts
from ctypes import (
    c_int,
    c_char_p,
    c_short,
    byref,
)
anc = ANC300()
ato_pos_start = 0
ato_pos_end = 2500 #ie 360deg
ato_pos_step = 20 #at roomtemp, 60V and f=1000Hz, step ~ 0.01deg
up_down = 'd' # set to up, to set to down replace 'u' with 'd'

setVoltage = {'x': 60} # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'x': 1000} # freq in Hz

anc.V = setVoltage #This sets the voltage for the sweep. 
anc.freq = setFreq #This sets the frequency for the sweep.

# Static Temperature:
measure_temp = False  # Do we actually want to measure Temperature here (Connect to Lakeshore via GPIB)?
temperature = 20e-3  # (Kelvin) Manual Temperature Record (For No Lakeshore Access)


# Folder To Save Files to:
exp_name = 'before_DR4_trans_remove_rod_water_rotate_addwasher'
filepath = p.home()/'Desktop'/'ORGAN_15GHz'/exp_name

# CSV file inside filepath containing VNA sweep/mode parameters in format:
# fcentral, fspan, bandwidth, npoints, naverages, power
runfile = p('run1.csv')

# Send error notifications to email addresses:
warn_email_list = ['21727308@student.uwa.edu.au']

# Other Settings:
sweep_type = "phi_pos"

# Additional VNA Settings
# (GPIB Settings are now located in /cryolib/vna_xxx)
channel = "1" #VNA Channel Number


# Temperature Controller Settings
LAKE_gpib = "GPIB2::16::INSTR"
LAKE_device_id = "LSCI,MODEL370,370732,04102008"
LAKE_channel = "8"

# SCRIPT STARTS HERE

warnings.filterwarnings('ignore', '.*GUI is implemented*') # Suppress Matplotlib warning
filepath = os.path.normpath(filepath)  # Convert pathname to look like a normal pathname for this OS

plt.ion()
fig = plt.figure("VNA DOWNLOAD")
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


# Starting Scan:
ato_pos_vals = np.arange(ato_pos_start, ato_pos_end + ato_pos_step, ato_pos_step)

print("Running Sweep over Phi = [" + str(ato_pos_start) + ", " + str(ato_pos_end) + "], with step = " +
      str(ato_pos_step) + " (" + str(len(ato_pos_vals)) + " sweeps)")

vnass.set_module(channel, warn_email_list) # Reset VNA Module
vnass.establish_connection()    # Establish connection to VNA


if measure_temp:
    print("Preparing Lakeshore for active Temperature Measurement")
    lakesm.connect(LAKE_gpib, LAKE_device_id)  # Prepare lakeshore if actively measuring temperature
    
# Run over step (phi) values
# Attocube code begins
for ato_pos in ato_pos_vals:
    print("Set position to ato_pos = " + str(ato_pos) + " " + "Steps")
    idx = list(ato_pos_vals).index(ato_pos)
    ato_step = ato_pos_step  #ato_pos - ato_pos_vals[idx - 1]
    if ato_pos == 0 or idx == 0: #since send a 0 instructs the stage to move continuously
        anc.stop()
        anc.ground()
    else:
        anc.step('x', ato_step, up_down)
        time.sleep(ato_step/setFreq['x']+0.5)
    time.sleep(0.1)  # Just wait a sec to stabilize
# Attocube code ends

    # Sweep over vna modes
    for mode in mode_list:
        sweep_data = vnass.sweep(mode)  # Do a sweep with these parameters

        fcent = mode[0]
        fspan = mode[1]
        bandwidth = mode[2]
        npoints = int(mode[3])
        power = mode[4]
        naverages = mode[5]

        if measure_temp:
            temperature = lakesm.get_temp(LAKE_channel)

        # Processing Starts here
        freq_data = gen.get_frequency_space(fcent, fspan, npoints)  # Generate list of frequencies

        fig.clf()
        ax = fig.add_subplot(111)
        ax.set_title("ato_pos = %.1f, f = %.3f GHz" % (ato_pos, fcent/1e9), fontsize=16)
        ax.plot(freq_data/1e9, gen.complex_to_dB(sweep_data), "g")
        ax.set_ylabel('S21 [dB]')
        ax.set_xlabel('Frequency [GHz]')
        #ax.xaxis.set_major_formatter(mtick.FormatStrFormatter('%2.2e'))
        plt.axis('tight')
        plt.draw()

        if list(mode_list).index(mode) == 0:
            ready_data = np.transpose(sweep_data)
        else:
            ready_data = np.vstack((ready_data, np.transpose(sweep_data)[1:]))

        t = datetime.now(timezone('Australia/Perth')).strftime(fmt)
    with h5py.File(filepath/p(exp_name + '.hdf5'), 'a') as f:
        try:
            if f[str(ato_pos)]:
                del(f[str(ato_pos)])
        except:
            None

        full_freq = np.linspace(mode_list[0][0]-fspan//2,fcent + fspan//2,ready_data.shape[0]) #freq list in Hz
        dset = f.create_dataset(str(ato_pos), data = ready_data, compression='gzip', compression_opts=6)  # VNA dset
        try:
            f['Freq']
        except:
            fdset = f.create_dataset('Freq', data=full_freq, compression='gzip', compression_opts=6)
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
            fdset.attrs['ato_voltage'] = setVoltage['x']
            fdset.attrs['ato_freq'] = setFreq['x']
        dset.attrs['ato_step'] = ato_step
        dset.attrs['ato_pos'] = ato_pos
        dset.attrs['temp'] = temperature
        dset.attrs['time'] = t

if measure_temp:
    lakesm.disconnect() # Disconnect from Lakeshore if actively measured temperature

print("Closing connection to Stepper Motor ", anc.close())

print("ALL VALUES RECORDED. SWEEP COMPLETE.")
