_author__ = 'Aaron Quiskamp'
import warnings
import time
import numpy as np
import cryolib.general as gen
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from lmfit.model import load_modelresult
import h5py
from pathlib import Path as p
import pyvisa
import vna_single_sweep as vnass
import DAQ_functions as df
matplotlib.use('TkAgg')
rm = pyvisa.ResourceManager()
#import lakeshore_temp as lakesm
filepath = p.home()/p('Desktop/VNA/ORGANattocube/follow_mode_test_2')
mode_map = load_modelresult(filepath/'tm010_model.sav')

#Connect attocube
up_down = 'u' # set to up, to set to down replace 'u' with 'd'
setVoltage = 60 # key-value pair, x is axis, '60' is voltage Volts
setFreq = 1000 # freq in Hz
ato = rm.open_resource("ASRL3::INSTR") #usually
ato.write("setv 1 "+str(setVoltage))
ato.write("setf 1 "+str(setFreq))

#VNA settings
channel = "1" #VNA Channel Number
warn_email_list = ['21727308@student.uwa.edu.au']
vnass.set_module(channel, warn_email_list) # Reset VNA Module
vnass.establish_connection()    # Establish connection to VNA
sweep_type = "ORGAN_14.6-16.5GHz"

#Initial Sweep
vna_fc = 15935650000
vna_span = 100000000
vna_ifb = 300
vna_pts = 1601
vna_ave = 1
vna_pow = 0

#sweep VNA
params = [vna_fc, vna_span, vna_ifb, vna_pts, vna_ave, vna_pow]  # sweep parameters
vna_sweep_data = vnass.sweep(params)  # data points

#peakfinder settings
peakheight = -70 # gets updated every sweep
prom = 5

ato_pos = 0 #start pos
max_ato_pos = 200 #end pos

while ato_pos < max_ato_pos:
    print("Stepping motor by " + str(ato_pos) + " steps")
    if ato_pos == 0:
        ato.write("stop")
    else:
        ato.write("setm 1 stp")
        ato.write("step" + up_down + " " + "1" + " " + str(ato_pos))  # steps determined by mode map
        time.sleep(ato_pos / setFreq + 0.1)  # need to sleep otherwise grounds instantly
        ato.write("setm 1 gnd")
        vna_fc = next_vna_fc
        time.sleep(0.5)
    #Sweep
    vna_span = 80000000
    vna_ifb = 300
    vna_pts = 1601
    vna_ave = 1
    vna_pow = 0
    vna_rbw = vna_span / (vna_pts - 1)

    #sweep VNA
    params = [vna_fc, vna_span, vna_ifb, vna_pts, vna_ave, vna_pow]  # sweep parameters
    vna_sweep_data = vnass.sweep(params)  # data points
    vna_freq_points = gen.get_frequency_space(vna_fc, vna_span, vna_pts)  # Generate list of frequencies
    vna_ready_data = np.transpose(vna_sweep_data)

    # Fit to the data
    mag_data = np.sqrt(vna_ready_data[:, 0] ** 2 + vna_ready_data[:, 1] ** 2)
    mag_data_db = 20 * np.log10(mag_data)

    #3db data to input as guess for fit
    f0, w3db, Q3db, peak_height, pheight_db = df.peakfinder(mag_data_db,vna_freq_points, prom, peakheight)
    #peakheight = pheight_db -10 # set peak height threshold for next pos in loop
    print(f0, w3db, Q3db, peak_height, pheight_db)

    #Q-fit
    Qfit, linewidth, fit_peak_db, fc_fit= df.Q_fit(mag_data, vna_freq_points, 1.5, f0[0],w3db[0], peak_height[0], True)

    # file name
    sweep_type_stamp = sweep_type
    time_stamp = "time=" + "{:.1f}".format(time.time())
    fcent_stamp = "fcent=" + str(int(vna_fc))
    fspan_stamp = "fspan=" + str(int(vna_span))
    npoints_stamp = "npoints=" + str(vna_pts)
    ato_pos_stamp = "atp_pos=" + str(ato_pos)

    filename = sweep_type_stamp
    filename += "_" + time_stamp
    filename += "_" + fcent_stamp
    filename += "_" + fspan_stamp
    filename += "_" + npoints_stamp
    filename += "_" + ato_pos_stamp

    full_filename = p(filepath / (filename + '.hdf5'))

    # write vna sweep to hdf5 file
    with h5py.File(full_filename, 'w') as f:
        dset = f.create_dataset('VNA', (vna_pts, 2), dtype=np.float64, compression='lzf') #VNA dset
        dset[:, :] = vna_ready_data
        dset.attrs['vna_fc'] = vna_fc  # this is from the mode map
        dset.attrs['time'] = time_stamp.split('=')[1]
        dset.attrs['vna_pow'] = vna_pow
        dset.attrs['vna_span'] = vna_span
        dset.attrs['vna_pts'] = vna_pts
        dset.attrs['vna_ave'] = vna_ave
        dset.attrs['vna_rbw'] = vna_rbw
        dset.attrs['vna_ifb'] = vna_ifb
        dset.attrs['ato_pos'] = ato_pos
        dset.attrs['Q3db'] = Q3db
        dset.attrs['Qfit'] = Qfit
        dset.attrs['fit_peak_db'] = fit_peak_db
        dset.attrs['linewidth'] = linewidth

    if up_down == 'u':
        next_vna_fc = df.roundup(f0[0] - 0.4 * linewidth, vna_rbw)
    else:
        next_vna_fc = df.roundup(f0[0] + 0.4 * linewidth, vna_rbw)
    next_ato_pos = int(round(abs(mode_map.eval(x = next_vna_fc) - mode_map.eval(x = f0[0]))))
    ato_pos = ato_pos + next_ato_pos
    print('f_c: ' + str(f0[0]) + ',lw: ' + str(int(linewidth)) + ', Next f_c: '
          + str(int(next_vna_fc)) + ', Next ato_step: ' + str(ato_pos))
    time.sleep(1)


