# THIS SCRIPTS INITIATES A frequency Sweep Using Agilent VNA

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


import vna_single_sweep as vnass
import lakeshore_temp as lakesm
#import amag_ramp as amagrp
sweep_type = "cal"

# Folder To Save Files to:
filepath = r"C:\Users\equslab\Desktop\ORGAN_15GHz\r_cal_amp_10_30"

# CSV file inside filepath containing VNA sweep/mode parameters in format:
# fcentral, fspan, bandwidth, npoints, naverages, power
runfile = r"run1.csv"

# Send error notifications to email addresses:
warn_email_list = ['maxim.goryachev@uwa.edu.au']


channel = "1"

warnings.filterwarnings('ignore', '.*GUI is implemented*') # Suppress Matplotlib warning
filepath = os.path.normpath(filepath)  # Convert pathname to look like a normal pathname for this OS

plt.ion()
fig = plt.figure("VNA DOWNLOAD")
plt.draw()

mode_list = np.loadtxt(filepath + "\\" + runfile, dtype='f8,f8,f8,i,i,f8', delimiter=',')
mode_list2 = mode_list

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

vnass.set_module(channel, warn_email_list) # Reset VNA Module
vnass.establish_connection()    # Establish connection to VNA

mnum = 0
for mode in mode_list:
    sweep_data = vnass.sweep(mode)  # Do a sweep with these parameters

    fcent = mode[0]
    fspan = mode[1]
    bandwidth = mode[2]
    npoints = int(mode[3])
    naverages = int(mode[4])
    power = mode[5]

       # if measure_temp:
        #    temperature1 = lakesm.get_temp(LAKE_channel1)
         #   temperature2 = lakesm.get_temp(LAKE_channel2)

        # Processing Starts here
    freq_data = gen.get_frequency_space(fcent, fspan, npoints)  # Generate list of frequencies
    ready_data = np.transpose(sweep_data)   # Get a transposed version of sweep_data for saving

    sweep_type_stamp = "swtype=" + sweep_type
    time_stamp = "time=" + "{:.1f}".format(time.time())
    #temp_stamp1 = "temp=" + "{:.4e}".format(temperature1)
    #temp_stamp2 = "temp2=" + "{:.4e}".format(temperature2)
    #temp_static_stamp = "temp-active=" + str(measure_temp)
    power_stamp = "power=" + str(power)
    fcent_stamp = "fcent=" + str(int(fcent))
    fspan_stamp = "fspan=" + str(int(fspan))
    npoints_stamp = "npoints=" + str(int(npoints))
    naverages_stamp = "naverages=" + str(int(naverages))
    #bfield_stamp = "b=" + str(bfield)
    bandwidth_stamp = "bandwidth=" + str(bandwidth)

    filename = "vna"
    filename += "_" + sweep_type_stamp
    filename += "_" + time_stamp
    #filename += "_" + temp_stamp1
    filename += "_" + power_stamp
    filename += "_" + fcent_stamp
    filename += "_" + fspan_stamp
    filename += "_" + npoints_stamp
    #filename += "_" + bfield_stamp

    full_filename = filepath + "\\" + filename + ".txtc"
    LS = '\n'

    text_file = open(full_filename, "w") # saving to text file

    text_file.write("VNA_DEVICE_ID=%s%s" % (vnass.device_id, LS))
    text_file.write(sweep_type_stamp + LS)
    text_file.write(time_stamp + LS)
    #text_file.write(temp_stamp1 + LS)
    #text_file.write(temp_stamp2 + LS)
    #text_file.write(temp_static_stamp + LS)
    text_file.write(power_stamp + LS)
    text_file.write(fcent_stamp + LS)
    text_file.write(fspan_stamp + LS)
    text_file.write(npoints_stamp + LS)
    text_file.write(naverages_stamp + LS)
    text_file.write(bandwidth_stamp + LS)
    #text_file.write(bfield_stamp + LS)

    text_file.write("DATA>>" + LS)

    for n in ready_data:
        text_file.write("%1.6e,%1.6e%s" % (n[0], n[1], LS))

    text_file.close()

    fig.clf()
    ax = fig.add_subplot(111)
    ax.set_title("T = %.0f sec, f = %.4e (%d) Hz" % (time.time(), fcent, fcent), fontsize=16)
    ax.plot(freq_data, gen.complex_to_dB(sweep_data), "g")
    ax.set_ylabel('S21 [dB]')
    ax.set_xlabel('Frequency [Hz]')
    ax.xaxis.set_major_formatter(mtick.FormatStrFormatter('%2.2e'))
    plt.axis('tight')
    plt.draw()
