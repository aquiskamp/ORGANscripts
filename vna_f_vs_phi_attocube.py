__author__ = 'Aaron'
__version__ = '20.03.2015_1.0'

# THIS SCRIPTS INITIATES A frequency vs B-field Sweep Using Agilent VNA and American Magnetics
import warnings
import os
import time
import numpy as np
import cryolib.general as gen

import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from prettytable import PrettyTable

from attocube.attocube import ANC300
anc = ANC300()
import vna_single_sweep as vnass
import lakeshore_temp as lakesm

#New code starts
from ctypes import (
    c_int,
    c_char_p,
    c_short,
    byref,
)

ato_pos_start = 0
ato_pos_end = 5000 #ie 360deg
ato_pos_step = 30 #at roomtemp, 60V and f=1000Hz, step ~ 0.01deg
up_down = 'd' # set to up, to set to down replace 'u' with 'd'

setVoltage = {'x': 60} # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'x': 1000} # freq in Hz

anc.V = setVoltage #This sets the voltage for the sweep. 
anc.freq = setFreq #This sets the frequency for the sweep.

# Static Temperature:
measure_temp = False  # Do we actually want to measure Temperature here (Connect to Lakeshore via GPIB)?
temperature = 20e-3  # (Kelvin) Manual Temperature Record (For No Lakeshore Access)


# Folder To Save Files to:
filepath = r'C:\Users\equslab\Desktop\ORGAN_15GHz\ORGAN_cal_refl_before_DR4'

# CSV file inside filepath containing VNA sweep/mode parameters in format:
# fcentral, fspan, bandwidth, npoints, naverages, power
runfile = r"run1.csv"


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

mode_list = np.loadtxt(filepath + "\\" + runfile, dtype='f8,f8,f8,i,i,f8', delimiter=',')

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
    ato_step = ato_pos - ato_pos_vals[idx - 1]
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

        if measure_temp:
            temperature = lakesm.get_temp(LAKE_channel)

        # Processing Starts here
        freq_data = gen.get_frequency_space(fcent, fspan, npoints)  # Generate list of frequencies
        ready_data = np.transpose(sweep_data)   # Get a transposed version of sweep_data for saving

        sweep_type_stamp = "swtype=" + sweep_type
        time_stamp = "time=" + "{:.1f}".format(time.time())
        temp_stamp = "temp=" + "{:.4e}".format(temperature)
        temp_static_stamp = "temp-active=" + str(measure_temp)
        power_stamp = "power=" + str(power)
        fcent_stamp = "fcent=" + str(int(fcent))
        fspan_stamp = "fspan=" + str(int(fspan))
        npoints_stamp = "npoints=" + str(npoints)
        naverages=1
        naverages_stamp = "naverages=" + str(int(naverages))
        ato_pos_stamp = "atp_pos=" + str(ato_pos)
        bandwidth_stamp = "bandwidth=" + str(bandwidth)

        filename = "vna"
        filename += "_" + sweep_type_stamp
        filename += "_" + time_stamp
        filename += "_" + temp_stamp
        filename += "_" + power_stamp
        filename += "_" + fcent_stamp
        filename += "_" + fspan_stamp
        filename += "_" + npoints_stamp
        filename += "_" + ato_pos_stamp

        full_filename = filepath + "\\" + filename + ".txtc"
        LS = '\n'

        text_file = open(full_filename, "w") # saving to text file

        text_file.write("VNA_DEVICE_ID=%s%s" % (vnass.device_id, LS))
        text_file.write(sweep_type_stamp + LS)
        text_file.write(time_stamp + LS)
        text_file.write(temp_stamp + LS)
        text_file.write(temp_static_stamp + LS)
        text_file.write(power_stamp + LS)
        text_file.write(fcent_stamp + LS)
        text_file.write(fspan_stamp + LS)
        text_file.write(npoints_stamp + LS)
        text_file.write(naverages_stamp + LS)
        text_file.write(bandwidth_stamp + LS)
        text_file.write(ato_pos_stamp + LS)

        text_file.write("DATA>>" + LS)

        for n in ready_data:
            text_file.write("%1.6e,%1.6e%s" % (n[0], n[1], LS))

        text_file.close()

        fig.clf()
        ax = fig.add_subplot(111)
        ax.set_title("ato_pos = %.5f T, f = %.4e (%d) Hz" % (ato_pos, fcent, fcent), fontsize=16)
        ax.plot(freq_data, gen.complex_to_dB(sweep_data), "g")
        ax.set_ylabel('S11 [dB]')
        ax.set_xlabel('Frequency [Hz]')
        ax.xaxis.set_major_formatter(mtick.FormatStrFormatter('%2.2e'))
        plt.axis('tight')
        plt.draw()


if measure_temp:
    lakesm.disconnect() # Disconnect from Lakeshore if actively measured temperature

print("Closing connection to Stepper Motor ", anc.close())

print("ALL VALUES RECORDED. SWEEP COMPLETE.")
