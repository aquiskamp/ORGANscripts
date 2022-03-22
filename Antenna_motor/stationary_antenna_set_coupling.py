__author__ = 'Aaron Quiskamp'
### Goal is to set coupling of a particular target mode in open loop using linear stage

import time
import numpy as np
import matplotlib.pyplot as plt
from prettytable import PrettyTable
import vna_single_sweep as vnass
import cryolib.general as gen
from pathlib import Path as p
from coupling_functions import *
from attocube.attocube_usb import ANC300
import h5py
from tqdm import tqdm

anc = ANC300()
target_beta = 1.5
beta_error_window = 0.1 #amount either side of target beta that is acceptable
beta_upper = target_beta + beta_error_window
beta_lower = target_beta - beta_error_window
step_size_multiple = 5 #coarse step size ie 1 step is n individual motor steps

# Folder To Save Files to:
exp_name = 'test_antenna'
filepath = p.home()/'Desktop'/'ORGAN_15GHz'/'Antenna_motor'/exp_name

# fcentral, fspan, bandwidth, npoints, naverages, power
runfile = p("run1.csv")

up_down = 'u' # set to up, to set to down replace 'u' with 'd'
setVoltage = {'x': 60} # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'x': 1000} # freq in

anc.freq(setFreq)
anc.V(setVoltage)
anc.ground()
#anc.step('x',1000,'u')


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

vnass.set_module()  # Reset VNA Module
vnass.establish_connection()  # Establish connection to VNA

# Sweep over vna modes
for mode in mode_list:
    sweep_data = vnass.sweep(mode)  # Do a sweep with these parameters
    db_data = gen.complex_to_dB(sweep_data)
    ready_data = np.transpose(sweep_data)

    fcent,fspan,bandwidth,npoints,power,average = mode

    # Processing Starts here
    freq_data = gen.get_frequency_space(fcent, fspan, npoints)  # Generate list of frequencies
    freq_data_GHz = freq_data/1e9

    dips, f0, dips_dict = dipfinder(db_data,freq_data,p_width=30, prom=2, Height=20)
    best_window = 0.02
    plot_freq_vs_db_mag(freq_data_GHz,db_data,f0[0])
    ######### fit to reflection dip #############
    fit_dict = test_refl_fit(ready_data,freq_data_GHz,dips[0],best_window,np.linspace(0,60,30),filepath)
    powerbeta = fit_dict['powerbeta']
    beta = fit_dict['beta']
    print(f'The current beta={beta}, and the power_beta={powerbeta}')
    while (beta_lower>=beta) or (beta>=beta_upper):
        print(f'The current beta={beta}, and the power_beta={powerbeta}')
        if beta<beta_lower:
            print(f'beta<{beta_lower} so move antenna in to achieve beta_target=[{beta_lower},{beta_upper}]')
            anc.step('x',10,'d')

        elif beta>beta_upper:
            print(f'beta>{beta_upper} so move antenna out to achieve beta_target=[{beta_lower},{beta_upper}]')
            anc.step('x', 10, 'u')
        #update mode params
        mode = [f0[0], fspan, bandwidth, npoints, power, average]
        sweep_data = vnass.sweep(mode)
        ready_data = np.transpose(sweep_data)  # Get a transposed version of sweep_data for saving
        db_data = gen.complex_to_dB(sweep_data)
        freq_data = gen.get_frequency_space(f0[0], fspan, npoints)  # Generate list of frequencies
        freq_data_GHz = freq_data / 1e9
        dips, f0, dips_dict = dipfinder(db_data, freq_data, p_width=30, prom=2, Height=20)
        fit_dict = test_refl_fit(ready_data, freq_data_GHz, dips[0], best_window,np.linspace(0,60,30),filepath)
        powerbeta = fit_dict['powerbeta']
        beta = fit_dict['beta']
        best_window = fit_dict['best_window']
        print(best_window)
        plot_freq_vs_db_mag(freq_data_GHz, db_data, f0[0])

    print(f'beta in range = [{beta_lower},{beta_upper}], so we do nothing')

print("Closing connection to Stepper Motor ", anc.close())

print("ALL VALUES RECORDED. SWEEP COMPLETE.")


