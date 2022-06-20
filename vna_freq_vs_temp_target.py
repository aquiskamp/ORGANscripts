__author__ = 'Aaron'

import warnings
import time
import numpy as np
import cryolib.general as gen
import matplotlib
import matplotlib.pyplot as plt
from prettytable import PrettyTable
from attocube.attocube_usb import ANC300
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

db_min=-50
db_max=-100

time_step = 30 #wait time between steps
temp_target = 4 # in kelvin

anc = ANC300()
measure_temp = True  # Do we actually want  to measure Temperature here (Connect to Lakeshore via GPIB)?
temperature = 4  # (Kelvin) Manual Temperature Record (For No Lakeshore Access)
measure_cap = True
cap = 0
cd_plot = True #colour density plot

# Folder To Save Files to:
exp_name = 'RT_4K_cooldown_loops'
filepath = p.home()/'Desktop'/'Sapphire_wedges'/exp_name

# fcentral, fspan, bandwidth, npoints, naverages, power
runfile = filepath/'run1.csv'

# Temperature Controller Settings
LAKE_gpib = "GPIB2::13::INSTR"
LAKE_device_id = "LSCI,MODEL340,342638,061407"
LAKE_channel = "8"

# SCRIPT STARTS HERE
warnings.filterwarnings('ignore', '.*GUI is implemented*') # Suppress Matplotlib warning
plt.ion()
fig = plt.figure("VNA DOWNLOAD")
plt.draw()

if cd_plot:
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

vnass.set_module() # Reset VNA Module
vnass.establish_connection()    # Establish connection to VNA

if measure_temp:
    print("Preparing Lakeshore for active Temperature Measurement")
    lakesm.connect(LAKE_gpib, LAKE_device_id)  # Prepare lakeshore if actively measuring temperature
    temperature = lakesm.get_temp(LAKE_channel)
    print(f'Current temp is {temperature}K')

idx = 0
while temperature>temp_target:
    if measure_temp:
        temperature = lakesm.get_temp(LAKE_channel)
    if measure_cap:
        cap = anc.cap()
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
        plt.pause(0.1)

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
        dset = f.create_dataset(str(idx), data = ready_data, compression='gzip', compression_opts=6)  # VNA dset
        try:
            f['Freq']
        except:
            fdset = f.create_dataset('Freq', data=full_freq, compression='gzip', compression_opts=6)
            fdset.attrs['f_start'] = mode_list[0][0]  # this is from the mode map / next freq
            fdset.attrs['f_final'] = fcent
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

    if cd_plot:
        if idx % 5 == 0 and idx != 0:
            fig1.clf()
            ax1 = fig1.add_subplot(111)
            mag_data_db, freq, steps = ato_hdf5_parser(filepath / p(exp_name + '.hdf5'))
            colour = ax1.imshow(mag_data_db, extent=[steps[0], steps[-1], freq[0], freq[-1]],aspect=(0.8 * (steps[-1] - steps[0]) / (freq[-1] - freq[0])),
                                cmap=plt.cm.get_cmap('viridis'), origin='lower', norm=Normalize(vmin=db_min, vmax=db_max))
            ax1.set_xlabel(r'Steps')
            ax1.set_ylabel(r'Frequency (GHz)')
            cb = fig1.colorbar(colour, ax=ax1, fraction=0.0325, pad=0.04)
            cb.set_label('$|S_{21}|$ [dB]')
            cm.ScalarMappable()
            plt.title(exp_name)
            plt.draw()
            plt.pause(0.1)

if cd_plot:
    # save modemap
    pp = PdfPages(filepath / (exp_name + '_MODE_MAP.pdf'))
    fig1.savefig(pp, format='pdf', dpi=600)
    pp.close()

if measure_temp:
    lakesm.disconnect() # Disconnect from Lakeshore if actively measured temperature

print("Closing connection to Stepper Motor ", anc.close())
print("ALL VALUES RECORDED. SWEEP COMPLETE.")
