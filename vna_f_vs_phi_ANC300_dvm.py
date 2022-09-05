__author__ = 'Aaron'
'This script uses the ANC300 box and a res sensor stage that is connected to a DVM'

import warnings
import time
import numpy as np
import cryolib.general as gen
import matplotlib.pyplot as plt
from prettytable import PrettyTable
from attocube.attocube_usb import ANC300
import DVM.dvm as dvm
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
from useful_functions import *

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']
anc = ANC300()

db_min = -40
db_max = -80

# Folder To Save Files to:
exp_name = 'rt_run4_very_strong'
filepath = p.home()/'Desktop'/'Aaron'/'Experiments'/'run_1b'/exp_name

# fcentral, fspan, bandwidth, npoints, naverages, power
runfile = p('run1.csv')

ato_start = 0
ato_end = 10_000
ato_step = 30
total_steps = int((ato_end - ato_start) / ato_step) + 1
up_down = 'd'  # set to up, to set to down replace 'u' with 'd'

setVoltage = {'x': 45} # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'x': 500} # freq in
anc.freq(setFreq)
anc.V(setVoltage)
anc.ground()

# Static Temperature:
measure_temp = 0  # Do we actually want to measure Temperature here (Connect to Lakeshore via GPIB)?
temperature = 20e-3  # (Kelvin) Manual Temperature Record (For No Lakeshore Access)

# Temperature Controller Settings
LAKE_gpib = "GPIB0::13::INSTR"
LAKE_device_id = "LSCI,MODEL340,342638,061407"
LAKE_channel = "A"

# SCRIPT STARTS HERE
plt.ion()
fig = plt.figure("VNA DOWNLOAD")
plt.draw()
move_figure()

plt.ion()
fig1 = plt.figure("MODE MAP")
plt.draw()

# plt.ion()
# fig2 = plt.figure("RES SENSOR")
# plt.draw()
# plt.pause(1)

mode_list = np.loadtxt(filepath / runfile, dtype='f8,f8,f8,i,i,f8', delimiter=',')
if np.size(mode_list) == 1:  # In case we have only one mode
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
ato_pos_vals = np.arange(ato_start, ato_end + ato_step, ato_step)
print("Running Sweep over Phi = [%s,%s] Steps, with %s step size (%s sweeps)" %(ato_start, ato_end, ato_step, total_steps))

vnass.set_module()  # Reset VNA Module
vnass.establish_connection()  # Establish connection to VNA

dvm.connect() #connect to dvm
dvm_range = 100000
dvm_res = 1
dvm_val = dvm.read_4w_meas(dvm_range, dvm_res)  # stage position
dvm_list = np.array([])

if measure_temp:
    print("Preparing Lakeshore for active Temperature Measurement")
    lakesm.connect(LAKE_gpib, LAKE_device_id)  # Prepare lakeshore if actively measuring temperature

# Run over step (phi) values
# Attocube code begins
for idx, ato_pos in enumerate(tqdm(ato_pos_vals)):
    print(f'Moving to ato_pos:{ato_pos}, currently at {dvm_val}')
    if ato_pos == 0 or idx == 0:  # since send a 0 instructs the stage to move continuously
        anc.ground()
    else:
        anc.step('x',ato_step,up_down)
        time.sleep(0.5)  # need to sleep otherwise grounds instantly

    dvm_val = dvm.read_4w_meas(dvm_range,dvm_res) #stage position

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
        ax = fig.add_subplot(111)
        ax.set_title("ato_pos = %.1f, f = %.3f GHz" % (ato_pos, fcent / 1e9), fontsize=16)
        ax.plot(freq_data / 1e9, gen.complex_to_dB(sweep_data), "g")
        ax.set_ylabel(r'$S_{21}$ [dB]')
        ax.set_xlabel('Frequency [GHz]')
        plt.axis('tight')
        plt.draw()
        plt.pause(0.1)

        if list(mode_list).index(mode) == 0:
            ready_data = np.transpose(sweep_data)
        else:
            ready_data = np.vstack((ready_data, np.transpose(sweep_data)[1:]))

        t = datetime.now(timezone('Australia/Perth')).strftime(fmt)

    with h5py.File(filepath / p(exp_name + '.hdf5'), 'a') as f:
        try:
            if f[str(ato_pos)]:
                del (f[str(ato_pos)])
        except:
            None

        full_freq = np.linspace(mode_list[0][0] - fspan // 2, fcent + fspan // 2,ready_data.shape[0])  # freq list in Hz
        dset = f.create_dataset(str(ato_pos), data=ready_data, compression='gzip', compression_opts=6)  # VNA dset
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
            fdset.attrs['vna_rbw'] = fspan / (npoints - 1)
            fdset.attrs['vna_ifb'] = bandwidth
            fdset.attrs['nmodes'] = mode_list.shape[0]
            fdset.attrs['ato_voltage'] = setVoltage['x']
            fdset.attrs['ato_freq'] = setFreq['x']
            fdset.attrs['ato_step'] = ato_step
            fdset.attrs['total_steps'] = total_steps
        dset.attrs['ato_pos'] = dvm_val
        dset.attrs['temp'] = temperature
        dset.attrs['time'] = t

    dvm_list = np.append(dvm_list,dvm_val)

    # fig2.clf()
    # ax = fig2.add_subplot(111)
    # ax.set_title("ato_pos = %.1f, current_dvm = %.1f" % (ato_pos, dvm_val), fontsize=16)
    # ax.scatter(ato_pos_vals[:idx+1],dvm_list)
    # ax.set_ylabel(r'DVM reading')
    # ax.set_xlabel('ato_pos')
    # plt.axis('tight')
    # plt.draw()
    # plt.pause(0.1)


    if idx % 5 == 0 and idx != 0:
        fig1.clf()
        ax1 = fig1.add_subplot(111)
        mag_data_db, freq, ato_positions = ato_hdf5_parser(filepath / p(exp_name + '.hdf5'))
        phi = ato_positions // ato_step
        colour = ax1.imshow(mag_data_db, extent=[phi[0], phi[-1], freq[0], freq[-1]],aspect=(0.8 * (phi[-1] - phi[0]) / (freq[-1] - freq[0])),
                            cmap=plt.cm.get_cmap('viridis'), origin='lower', norm=Normalize(vmin=db_min, vmax=db_max))
        ax1.set_xlabel(r'Phi (Steps)')
        ax1.set_ylabel(r'Frequency (GHz)')
        cb = fig1.colorbar(colour, ax=ax1, fraction=0.0325, pad=0.04)
        cb.set_label('$|S_{21}|$ [dB]')
        cm.ScalarMappable()
        plt.title(exp_name)
        plt.draw()
        plt.pause(0.1)

if measure_temp:
    lakesm.disconnect()  # Disconnect from Lakeshore if actively measured temperature

# save modemap
pp = PdfPages(filepath / (exp_name + '_MODE_MAP.pdf'))
fig1.savefig(pp, format='pdf', dpi=600)
pp.close()

print("Closing connection to Stepper Motor ", anc.ground(), dvm.close())
print("ALL VALUES RECORDED. SWEEP COMPLETE.")
