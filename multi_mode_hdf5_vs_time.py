__author__ = 'Aaron'
'''Do multi mode script and return 3dB Qs'''

import time
import lakeshore_temp as lakesm
import numpy as np
import pandas as pd
import cryolib.general as gen
import matplotlib.pyplot as plt
from pathlib import Path as p
from prettytable import PrettyTable
import vna_single_sweep as vnass
from datetime import datetime
from pytz import timezone
import h5py
from tqdm import tqdm
from useful_functions import *
import matplotlib
from matplotlib.backends.backend_pdf import PdfPages
matplotlib.use('Qt5Agg')

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']

time_step = 1*30 #wait time between steps
timeout = time.time() + 10*3600  # seconds

# Folder To Save Files to:
exp_name = 'Nb3Sn_sputtered_RT'
filepath = p.home()/'Desktop'/'Aaron'/'Experiments'/'Al_clamshell'/exp_name

# fcentral, fspan, bandwidth, npoints, naverages, power
runfile = filepath/'run1.csv'

plt.ion()
fig = plt.figure("VNA")
plt.draw()
move_figure('desktop')

# Static Temperature:
measure_temp = 0 #Do we actually want to measure Temperature here (Connect to Lakeshore via GPIB)?
temperature = 4  # (Kelvin) Manual Temperature Record (For No Lakeshore Access)

# Temperature Controller Settings
LAKE_gpib = "GPIB1::13::INSTR"
LAKE_device_id = "LSCI,MODEL340,342638,061407"
LAKE_channel = "A"

if measure_temp:
    print("Preparing Lakeshore for active Temperature Measurement")
    lakesm.connect(LAKE_gpib, LAKE_device_id)  # Prepare lakeshore if actively measuring temperature
    temperature = lakesm.get_temp(LAKE_channel)


mode_list = np.loadtxt(runfile, dtype='f8,f8,f8,i,i,f8', delimiter=',')
if np.size(mode_list) == 1: # In case we have only one mode
    mode_list = np.asarray([mode_list])

# Plotting mode measurement settings as a nice table:
dat_dtype = {
    'names': ('Fcent (Hz)', 'Fspan (Hz)', 'BW (Hz)', 'NPoints', 'NAverages', 'Power (dBm)'),
    'formats': ('f8', 'f8', 'f8', 'i', 'i', 'f8')}
dat = np.zeros(6, dat_dtype)

table_data = PrettyTable(dat.dtype.names)
for row in mode_list:
    table_data.add_row(row)

print("Loaded Settings:")
print(table_data)

vnass.set_module() # Reset VNA Module
vnass.establish_connection()    # Establish connection to VNA

step_idx = 0

while True:
    if time.time() > timeout:
        break
    else:
        for idx,mode in enumerate(tqdm(mode_list)):
            sweep_data = vnass.sweep(mode)  # Do a sweep with these parameters
            ready_data = np.transpose(sweep_data)
            mag_data_db = 10*np.log10(ready_data[:,0]**2 + ready_data[:,1]**2)

            fcent = mode[0]
            fspan = mode[1]
            bandwidth = mode[2]
            npoints = int(mode[3])
            naverages = mode[4]
            power = mode[5]
            freq_data = gen.get_frequency_space(fcent, fspan, npoints)  # Generate list of frequencies

            t = datetime.now(timezone('Australia/Perth')).strftime(fmt)

            fig, ax = plt.subplots(1, figsize=(16, 8))
            plt.plot(freq_data/1e9, mag_data_db, color='blue')
            plt.xlabel(r'Frequency (GHz)',fontsize=22)
            plt.ylabel('$|S_{21}|$ (dB)',fontsize=22)
            ax.tick_params(axis='x', labelsize=16)
            ax.tick_params(axis='y', labelsize=16)
            plt.title(f'f_0:{fcent/1e9}GHz')

            with h5py.File(filepath / p(exp_name + '.hdf5'), 'a') as f:
                dset = f.create_dataset('step_' + str(step_idx) + '_'+ (str(idx), data=ready_data, compression='gzip', compression_opts=6)  # VNA dset
                dset.attrs['time'] = t
                dset.attrs['temp'] = temperature
                try:
                    f['Freq']:
                except:
                    fdset = f.create_dataset('Freq_'+ str(idx), data=freq_data, compression='gzip', compression_opts=6)
                    fdset.attrs['f_cent'] = fcent
                    fdset.attrs['vna_pow'] = power
                    fdset.attrs['vna_span'] = fspan
                    fdset.attrs['vna_pts'] = npoints
                    fdset.attrs['vna_ave'] = naverages
                    fdset.attrs['vna_rbw'] = fspan / (npoints - 1)
                    fdset.attrs['vna_ifb'] = bandwidth
                    fdset.attrs['nmodes'] = mode_list.shape[0]
    step_idx += 1
    print(f'Current temp is {temperature}K')
    time.sleep(time_step)

if measure_temp:
    lakesm.disconnect() # Disconnect from Lakeshore if actively measured temperature
print('SWEEP FINISHED')
