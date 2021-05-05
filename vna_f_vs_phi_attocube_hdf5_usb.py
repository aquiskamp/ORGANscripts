__author__ = 'Aaron'

import warnings
import time
import pyvisa
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

#time.sleep(11*3600)

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']
matplotlib.use('TkAgg')

ato_pos_start = 0
ato_pos_end = 30000 #ie
ato_pos_step = 500 #at roomtemp, 60V and f=1000Hz, step ~ 0.01deg
up_down = 'd' # set to up, to set to down replace 'u' with 'd'

setVoltage = 50 # key-value pair, x is axis, '60' is voltage Volts
setFreq = 1000 # freq in Hz

rm = pyvisa.ResourceManager()

inst = rm.open_resource('ASRL3::INSTR') #usually COM3
inst.write("setv 1 "+str(setVoltage))
inst.write("setf 1 "+str(setFreq))

# Static Temperature:
measure_temp = False  # Do we actually want to measure Temperature here (Connect to Lakeshore via GPIB)?
temperature = 20e-3  # (Kelvin) Manual Temperature Record (For No Lakeshore Access)

# Folder To Save Files to:
exp_name = 'trans_r2d2_tighten_stage_down'
filepath = p.home()/'Desktop'/'ORGAN_15GHz'/exp_name

# CSV file inside filepath containing VNA sweep/mode parameters in format:
# fcentral, fspan, bandwidth, npoints, naverages, power
runfile = p('run1.csv')

# Send error notifications to email addresses:
warn_email_list = ['21727308@student.uwa.edu.au']

# Other Settings:
sweep_type = "phi_pos"

# Additional VNA Settings
channel = "1" #VNA Channel Number

# Temperature Controller Settings
LAKE_gpib = "GPIB2::16::INSTR"
LAKE_device_id = "LSCI,MODEL370,370732,04102008"
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
    # print('Capacitance is: '+ str(anc.cap))
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
        naverages = mode[4]
        power = mode[5]

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

    with h5py.File(filepath/p(exp_name + '_1_.hdf5'), 'a') as f:
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
            fdset.attrs['ato_step'] = ato_step
        dset.attrs['ato_pos'] = ato_pos
        dset.attrs['temp'] = temperature
        dset.attrs['time'] = t
    time.sleep(60*2)
    # print('Script is sleeping for 300 seconds')
    # if idx%5 == 0:
    #     print('Poisitoner is sleeping for 5 mins...')
    #     time.sleep(60*5)
if measure_temp:
    lakesm.disconnect() # Disconnect from Lakeshore if actively measured temperature

print("Closing connection to Stepper Motor ", anc.close())

print("ALL VALUES RECORDED. SWEEP COMPLETE.")
