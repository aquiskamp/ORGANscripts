__author__ = 'Aaron Quiskamp'
### Goal is to set coupling of a particular target mode in open loop using linear stage

import time
import numpy as np
import pyvisa
import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
from prettytable import PrettyTable
import vna_single_sweep as vnass
import cryolib.general as gen
from pathlib import Path as p
from coupling_functions import *
from resonator_tools import circuit
import h5py
from tqdm import tqdm
from scipy.signal import find_peaks

def dipfinder(data,freq,p_width, prom, Height):
    # Find peaks with data given as db
    dips = find_peaks(-data, prominence=prom, height=Height, width=p_width)
    f0 = freq[dips[0]]
    return dips[0], f0, dips

def find_nearest_pos(a, a0):
    "position in nd array `a` closest to the scalar value `a0`"
    idx = np.abs(a - a0).argmin()
    return idx

def power_beta(on,off):
    return (1-np.sqrt(10**(on/10)/10**(off/10)))/(1+np.sqrt(10**(on/10)/10**(off/10)))

def refl_fit(data,freq_data,window,delay_arr):
    save_dir = str(filepath) + '/delay_refl_fit/'
    f_guess = freq_data[dips]
    chi = np.empty((0,3))
    p(save_dir).mkdir(parents=True, exist_ok=True)

    try:
        for idx,val in enumerate(window):
            minpos = find_nearest_pos(freq_data,f_guess-val/2)
            maxpos = find_nearest_pos(freq_data,f_guess+val/2)
            f_data = freq_data[minpos:maxpos]
            phase_data = np.angle(data[:, 0] + 1j * data[:, 1])[minpos:maxpos]
            mag_data = np.abs(data[:, 0] + 1j * data[:, 1])[minpos:maxpos]
            z_data = mag_data*np.exp(1j*phase_data)
            port1 = circuit.reflection_port(f_data, z_data)

            for i in delay_arr:
                port1.autofit(electric_delay=i,fr_guess=f_guess)
                if port1.fitresults.get('chi_square') is not None:
                    chi = np.vstack((chi,[val,port1.fitresults['chi_square'],i]))
                else:
                    chi = np.vstack((chi,[val,1,i]))
    except:
        print(f'Not working')
    arg_min = chi[:,1].argmin()
    best_window, _, delay_min = chi[arg_min]
    minpos = find_nearest_pos(freq,f_guess-best_window/2)
    maxpos = find_nearest_pos(freq,f_guess+best_window/2)
    f_data = freq_data[minpos:maxpos]
    phase_data = np.angle(data[:, 0] + 1j * data[:, 1])[minpos:maxpos]
    mag_data = np.abs(data[:, 0] + 1j * data[:, 1])[minpos:maxpos]
    z_data = mag_data * np.exp(1j * phase_data)
    port1 = circuit.reflection_port(f_data, z_data)
    port1.autofit(electric_delay=delay_min,fr_guess=f_guess)
    powerbeta = power_beta(20*np.log10(mag_data).min(),20*np.log10(mag_data).max())

    fit_dict = {}
    for key,value in port1.fitresults.items():
        fit_dict[key] = value
        fit_dict['beta'] = port1.fitresults['Qi']/port1.fitresults['Qc']
        fit_dict['powerbeta'] = powerbeta
    port1.plotall()

    return fit_dict

    # df = pd.DataFrame([fit_dict]) #write results to dict so we can export to csv
    # if phi==0:
    #     f = open(save_dir + 'refl_params.csv','w')
    #     f.close()
    # with open(save_dir + 'refl_params.csv','a') as f:
    #     df.to_csv(f, mode='a', header=f.tell()==0)
    # port1.plotallsave_delay(save_dir + 'phi = ' + str(phi_val)+'.pdf')
    # warnings.filterwarnings("ignore")

# Folder To Save Files to:
exp_name = 'test_antenna'
filepath = p.home()/'Desktop'/'ORGAN_15GHz'/'Antenna_motor'/exp_name

# fcentral, fspan, bandwidth, npoints, naverages, power
runfile = p("run1.csv")

wait_time = 1*15 #seconds

up_down = 'u' # set to up, to set to down replace 'u' with 'd'
setVoltage = 60 # key-value pair, x is axis, '60' is voltage Volts
setFreq = 1000 # freq in Hz

rm = pyvisa.ResourceManager()
anc_lin = rm.open_resource('COM3') #usually COM3
anc_lin.write('setv 1 60')
anc_lin.write('setf 1 1000')
anc_lin.write('setm 1 gnd')
#time.sleep(30)
#anc_lin.write('setm 1 gnd')

plt.ion()
fig = plt.figure("VNA")
plt.draw()

mode_list = np.loadtxt(filepath/runfile, dtype='f8,f8,f8,i,i,f8', delimiter=',')

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

vnass.set_module()  # Reset VNA Module
vnass.establish_connection()  # Establish connection to VNA

# Sweep over vna modes
for mode in mode_list:
    sweep_data = vnass.sweep(mode)  # Do a sweep with these parameters

    fcent,fspan,bandwidth,npoints,power,average = mode

    # Processing Starts here
    freq_data = gen.get_frequency_space(fcent, fspan, npoints)  # Generate list of frequencies
    freq_data_GHz = freq_data/1e9
    ready_data = np.transpose(sweep_data)  # Get a transposed version of sweep_data for saving
    db_data = gen.complex_to_dB(sweep_data)

    #fit to reflection dip
    dips, f0, dips_dict = dipfinder(db_data,freq_data,p_width=30, prom=5, Height=25)

    #refl_fit(ready_data,freq_data_GHz,[0.01,0.02,0.03,0.04],np.linspace(0,60,180))
    f_guess = freq_data_GHz[dips[0]]
    minpos = find_nearest_pos(freq_data_GHz, f_guess - 0.03 / 2)
    maxpos = find_nearest_pos(freq_data_GHz, f_guess + 0.03 / 2)
    f_data = freq_data_GHz[minpos:maxpos]
    phase_data = np.angle(ready_data[:, 0] + 1j * ready_data[:, 1])[minpos:maxpos]
    mag_data = np.abs(ready_data[:, 0] + 1j * ready_data[:, 1])[minpos:maxpos]
    z_data = mag_data * np.exp(1j * phase_data)
    port1 = circuit.reflection_port(f_data, z_data)
    port1.autofit(fr_guess=f_guess)
    port1.plotallsave_delay(filepath/'test.pdf')

    # fig.clf()
    # ax = fig.add_subplot(111)
    # ax.set_title("f = %.3f GHz" % (fcent / 1e9), fontsize=16)
    # ax.plot(freq_data/1e9, db_data, "g")
    # ax.scatter(freq_data[dips]/1e9,db_data[dips],marker='X',color='red',s=30)
    # ax.set_ylabel(r'$S_{21}$ [dB]')
    # ax.set_xlabel('Frequency [GHz]')
    # plt.axis('tight')
    # plt.draw()

print("Closing connection to Stepper Motor ", anc_lin.close())

print("ALL VALUES RECORDED. SWEEP COMPLETE.")


