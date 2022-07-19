__author__ = 'Aaron'
'''Do full freq sript and return 3dB Qs'''

import warnings
import time
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

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']

#Q3db params
prom = 5
peak_width = 5
rel = 0.1
window = 50
Height = -80 # in db

# Folder To Save Files to:
exp_name = 'cavity_to_amp_cal'
filepath = p.home()/'Desktop'/'Aaron'/'Experiments'/'Antenna_motor'/exp_name

# fcentral, fspan, bandwidth, npoints, naverages, power
runfile = filepath/'run1.csv'

# Static Temperature:
measure_temp = True  # Do we actually want to measure Temperature here (Connect to Lakeshore via GPIB)?
temperature = 4  # (Kelvin) Manual Temperature Record (For No Lakeshore Access)

# Temperature Controller Settings
LAKE_gpib = "GPIB0::13::INSTR"
LAKE_device_id = "LSCI,MODEL340,342638,061407"
LAKE_channel = "8"

if measure_temp:
    print("Preparing Lakeshore for active Temperature Measurement")
    lakesm.connect(LAKE_gpib, LAKE_device_id)  # Prepare lakeshore if actively measuring temperature
    temperature = lakesm.get_temp(LAKE_channel)

plt.ion()
fig = plt.figure("VNA DOWNLOAD")
plt.draw()

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

for mode in tqdm(mode_list):
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
    ax.set_title("f = %.3f GHz" % (fcent / 1e9), fontsize=16)
    ax.plot(freq_data / 1e9, gen.complex_to_dB(sweep_data), "g")
    ax.set_ylabel(r'$|S_{11}|$ [dB]')
    ax.set_xlabel('Frequency [GHz]')
    plt.axis('tight')
    plt.draw()
    plt.pause(0.1)

    if list(mode_list).index(mode) == 0:
        ready_data = np.transpose(sweep_data)
    else:
        ready_data = np.vstack((ready_data, np.transpose(sweep_data)[1:]))

    t = datetime.now(timezone('Australia/Perth')).strftime(fmt)

#Get 3db Q estimate for prominent modes
full_freq = np.linspace(mode_list[0][0] - fspan // 2, fcent + fspan // 2, ready_data.shape[0])  # freq list in Hz
mag_data_db = 10*np.log10(ready_data[:,0]**2 + ready_data:,1]**2)

try:
    peaks, f0s, Qs, peak_heights = full_freq_Q3db(mag_data_db,full_freq,prom,peak_width,rel,window,Height,full_freq[0],full_freq[-1])
    df = pd.DataFrame([f0s,Qs,peak_heights],columns=['f0s','Qs','peak_db'])

    fig, ax = plt.subplots(1, figsize=(16, 8))
    plt.plot(full_freq/1e9, mag_data_db)
    plt.plot(f0s/1e9, data[peaks], "x", color="C2", markersize=10)
    plt.xlabel(r'Frequency (GHz)')
    plt.ylabel('$|S_{21}|$ (dB)')
    plt.show()

    # save plot
    pp = PdfPages(filepath / (exp_name + '_full_freq.pdf'))
    fig.savefig(pp, format='pdf', dpi=600)
    pp.close()

    # save Qs
    df.to_csv('f0_vs_Q.csv',index=False)

except:
    print('Could not find Qs')


with h5py.File(filepath / p(exp_name + '.hdf5'), 'a') as f:
    dset = f.create_dataset('VNA', data=ready_data, compression='gzip', compression_opts=6)  # VNA dset
    fdset = f.create_dataset('Freq', data=full_freq, compression='gzip', compression_opts=6)
    fdset.attrs['f_start'] = mode_list[0][0]  # this is from the mode map / next freq
    fdset.attrs['f_final'] = fcent
    fdset.attrs['vna_pow'] = power
    fdset.attrs['vna_span'] = fspan
    fdset.attrs['vna_pts'] = npoints
    fdset.attrs['vna_ave'] = naverages
    fdset.attrs['vna_rbw'] = fspan / (npoints - 1)
    fdset.attrs['vna_ifb'] = bandwidth
    fdset.attrs['nmodes'] = mode_list.shape[0]
    fdset.attrs['time'] = t
    fset.attrs['temp'] = temperature

print('SWEEP FINISHED')
