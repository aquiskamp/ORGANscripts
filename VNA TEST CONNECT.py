_author__ = 'Aaron'
import warnings
import time
import numpy as np
import cryolib.general as gen
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
matplotlib.use('TkAgg')
import h5py
from pathlib import Path as p

import vna_single_sweep as vnass
#import lakeshore_temp as lakesm

#VNA settings
channel = "1" #VNA Channel Number
warn_email_list = ['21727308@student.uwa.edu.au']
vnass.set_module(channel, warn_email_list) # Reset VNA Module
vnass.establish_connection()    # Establish connection to VNA
sweep_type = "ORGAN_15.6-16.6GHz"

filepath = p.home()/p('Desktop')

#Set mode parameters
fcent = 16040000000
fspan = 10000000
if_bandwidth = 300
npoints = 1601
ave = 1
power = 0
bandwidth = fspan/(npoints-1)
fstart = fcent - fspan//2

plt.ion()
fig = plt.figure("VNA DOWNLOAD")
plt.draw()

params = [fcent,fspan,if_bandwidth,npoints,ave,power]

sweep_data = vnass.sweep(params) # data points
fcent_max = int(vnass.get_maxi()[2][0]) #new fcent based on max
freq_data = gen.get_frequency_space(fcent, fspan, npoints)  # Generate list of frequencies
ready_data = np.transpose(sweep_data)
print(fcent_max)

sweep_type_stamp = "swtype=" + sweep_type
time_stamp = "time=" + "{:.1f}".format(time.time())
power_stamp = "power=" + str(power)
fcent_stamp = "fcent=" + str(int(fcent))
fspan_stamp = "fspan=" + str(int(fspan))
npoints_stamp = "npoints=" + str(npoints)
naverages_stamp = "naverages=" + str(int(ave))
#ato_pos_stamp = "atp_pos=" + str(ato_pos)
bandwidth_stamp = "bandwidth=" + str(bandwidth)

filename = "vna"
filename += "_" + sweep_type_stamp
filename += "_" + time_stamp
filename += "_" + power_stamp
filename += "_" + fcent_stamp
filename += "_" + fspan_stamp
filename += "_" + npoints_stamp
#filename += "_" + ato_pos_stamp

full_filename = p(filepath/(filename + '.hdf5'))
print(full_filename)

#Plot
fig.clf()
ax = fig.add_subplot(111)
ax.set_title("f = %.4e Hz" % (fcent), fontsize=16)
ax.plot(freq_data, gen.complex_to_dB(sweep_data), "g")
ax.set_ylabel('S11 [dB]')
ax.set_xlabel('Frequency [Hz]')
ax.xaxis.set_major_formatter(mtick.FormatStrFormatter('%2.2e'))
plt.axis('tight')
plt.draw()

with h5py.File(full_filename,'w') as f:
    dset = f.create_dataset('Magnitude', (npoints,2), dtype=np.float64, compression='gzip',compression_opts=9)
    dset[:,:] = ready_data
    dset.attrs['fcent'] = fcent
    dset.attrs['fcent_max'] = fcent_max
    dset.attrs['time'] = time_stamp.split('=')[1]
    dset.attrs['power'] = power
    dset.attrs['fspan'] = fspan
    dset.attrs['npoints'] = npoints
    dset.attrs['naverages'] = ave
    dset.attrs['bandwidth'] = bandwidth
    dset.attrs['if_bandwidth'] = if_bandwidth
    #dset.attrs['ato_pos'] = ato_pos_stamp.split('=')[1]
    #add fftm data and attrs
    
f = h5py.File(full_filename,'r')
dset=f['Magnitude']
print(dset[:])
print(dset.attrs['fcent'])
print(dset.attrs['time'])
print(dset.attrs['power'])
print(dset.attrs['fspan'])
print(dset.attrs['npoints'])
print(dset.attrs['naverages'])
print(dset.attrs['bandwidth'])
print(dset.attrs['fcent_max'])
print(dset.attrs['if_bandwidth'])


