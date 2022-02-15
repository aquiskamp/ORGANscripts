__author__ = 'Aaron'

import warnings
import time
import numpy as np
import cryolib.general as gen
import matplotlib
import matplotlib.pyplot as plt
from prettytable import PrettyTable
from attocube.attocube import ANC300
import vna_single_sweep as vnass
import lakeshore_temp as lakesm
from pathlib import Path as p
from datetime import datetime
from pytz import timezone
import h5py
from attocube.ato_func import ato_hdf5_parser
from matplotlib import cm
from matplotlib.colors import Normalize
from tqdm import tqdm
from matplotlib.backends.backend_pdf import PdfPages

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']
matplotlib.use('TkAgg')

db_min=-60
db_max=-100

time_step = 60*3 #wait time between steps
timeout = time.time() + 12*3600  # seconds

anc = ANC300()
measure_temp = False  # Do we actually want  to measure Temperature here (Connect to Lakeshore via GPIB)?
temperature = 4  # (Kelvin) Manual Temperature Record (For No Lakeshore Access)
measure_cap = False
cap = 0

# Folder To Save Files to:
exp_name = 'ramp_magnet_down'
filepath = p.home()/'Desktop'/'ORGAN_15GHz'/'70mm_cavity'/exp_name

# CSV file inside filepath containing VNA sweep/mode parameters in format:
# fcentral, fspan, bandwidth, npoints, naverages, power
runfile = filepath/'run1.csv'

# Send error notifications to email addresses:
warn_email_list = ['21727308@student.uwa.edu.au']

# Other Settings:
sweep_type = "freq_vs_temp"

# Additional VNA Settings
channel = "1" #VNA Channel Number

# Temperature Controller Settings
LAKE_gpib = "GPIB3::13::INSTR"
LAKE_device_id = "LSCI,MODEL340,342638,061407"
LAKE_channel = "8"

# SCRIPT STARTS HERE
warnings.filterwarnings('ignore', '.*GUI is implemented*') # Suppress Matplotlib warning
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

vnass.set_module(channel, warn_email_list) # Reset VNA Module
vnass.establish_connection()    # Establish connection to VNA

if measure_temp:
    print("Preparing Lakeshore for active Temperature Measurement")
    lakesm.connect(LAKE_gpib, LAKE_device_id)  # Prepare lakeshore if actively measuring temperature

timeout = time.time() + 8*3600  # seconds
idx = 0
while True:
    if time.time() > timeout:
        break
    else:
        if measure_temp:
            temperature = lakesm.get_temp(LAKE_channel)
        if measure_cap:
            cap = anc.cap['x']

        # Sweep over vna modes
        for mode in mode_list:
            sweep_data = vnass.sweep(mode)  # Do a sweep with these parameters

            fcent = mode[0]
            fspan = mode[1]
            bandwidth = mode[2]
            npoints = int(mode[3])
            naverages = mode[4]
            power = mode[5]

            # Processing Starts here
            freq_data = gen.get_frequency_space(fcent, fspan, npoints)  # Generate list of frequencies

            fig.clf()
            ax = fig.add_subplot(111)
            ax.set_title("T = %0.1fK f = %.3f GHz" % (temperature,fcent/1e9), fontsize=16)
            ax.plot(freq_data/1e9, gen.complex_to_dB(sweep_data), "g")
            ax.set_ylabel(r'$|S_{21}|$ [dB]')
            ax.set_xlabel('Frequency [GHz]')
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
            dset.attrs['temp'] = temperature
            dset.attrs['time'] = t
            dset.attrs['cap'] = cap
        idx += 1
        print(f'Current temp is {temperature}K')
        time.sleep(time_step)
if measure_temp:
    lakesm.disconnect() # Disconnect from Lakeshore if actively measured temperature

print("Closing connection to Stepper Motor ", anc.close())
print("ALL VALUES RECORDED. SWEEP COMPLETE.")