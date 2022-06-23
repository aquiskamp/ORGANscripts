__author__ = 'Aaron Quiskamp'
### Goal is to set coupling of a particular target mode in open loop using linear stage
### use unwrapped phase instead of fitting to phase

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

############# PARAMETERS
target_beta = 2
beta_error_window = 0.05 # amount either side of target beta that is acceptable
beta_upper = target_beta + beta_error_window #max beta
beta_lower = target_beta - beta_error_window #min beta
step_size = 50 # how many steps per iteration
dip_prom = 1 # prominence in dB of the reflection dip
dip_width = 0 # number of points wide in freq
max_height = 8 # must be below this value to be considered (dB)
#############

# Folder To Save Files to:
exp_name = 'rt_test'
filepath = p.home()/'Desktop'/'Aaron'/'Experiments'/'Antenna_motor'/exp_name

# fcentral, fspan, bandwidth, npoints, naverages, power
runfile = filepath/'run1.csv'

setVoltage = {'x': 45} # key-value pair, x is axis, '60' is voltage Volts
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
vnass.establish_connection_uphase()  # Establish connection to VNA

idx = 0
# Sweep over vna modes
for mode in mode_list:
    uphase,sweep_data = vnass.sweep_multi_trace(mode)  # Do a sweep with these parameters
    db_data = gen.complex_to_dB(sweep_data)
    ready_data = np.transpose(sweep_data)

    fcent,fspan,bandwidth,npoints,power,average = mode

    # Processing Starts here
    freq_data = gen.get_frequency_space(fcent, fspan, npoints)  # Generate list of frequencies
    freq_data_GHz = freq_data/1e9

    ######### dipfinder
    dips, f0, dips_dict = dipfinder(db_data,freq_data,p_width=dip_width, prom=dip_prom, Height=max_height)
    best_window = 0.03
    plot_freq_vs_db_mag_vs_phase(freq_data_GHz,db_data,uphase,f0[0])

    ######### fit to reflection dip
    fit_dict = test_refl_fit(ready_data,freq_data_GHz,dips[0],best_window,np.linspace(0,60,30),filepath)
    powerbeta = fit_dict['powerbeta']
    beta = fit_dict['beta']
    print(f'The current fitted beta={beta}, and the power_beta={powerbeta}')
    while (beta_lower>=beta) or (beta>=beta_upper):
        print(f'The current fitted beta={beta}, and the power_beta={powerbeta}')
        if beta<beta_lower:
            print(f'beta<{beta_lower} so move antenna in to achieve beta_target=[{beta_lower},{beta_upper}]')
            anc.step('x',step_size,'d')

        elif beta>beta_upper:
            print(f'beta>{beta_upper} so move antenna out to achieve beta_target=[{beta_lower},{beta_upper}]')
            anc.step('x', step_size, 'u')

        #update mode params
        mode = [f0[0], 50e6, bandwidth, npoints, power, average]
        uphase,sweep_data = vnass.sweep_multi_trace(mode)
        ready_data = np.transpose(sweep_data)  # Get a transposed version of sweep_data for saving
        db_data = gen.complex_to_dB(sweep_data)
        freq_data = gen.get_frequency_space(f0[0], fspan, npoints)  # Generate list of frequencies
        freq_data_GHz = freq_data / 1e9

        ########### dipfinder
        dips, f0, dips_dict = dipfinder(db_data, freq_data, p_width=dip_width, prom=dip_prom, Height=max_height)
        ########### refl fit
        fit_dict = test_refl_fit(ready_data, freq_data_GHz, dips[0], best_window,np.linspace(0,60,30),filepath)
        powerbeta = fit_dict['powerbeta']
        beta = fit_dict['beta']
        #best_window = fit_dict['best_window']
        #print(f'The best window was {best_window*1e3}MHz')
        plot_freq_vs_db_mag_vs_phase(freq_data_GHz, db_data, uphase, f0[0])
        plt.pause(0.1)

    print(f'beta in range = [{beta_lower},{beta_upper}], SUCCESS!')
    ############ save data
    with h5py.File(filepath / p(exp_name + '.hdf5'), 'a') as f:
        dset = f.create_dataset("s21", data=ready_data, compression='gzip', compression_opts=6)
        dset1 = f.create_dataset("uphase", data=uphase, compression='gzip', compression_opts=6)
        dset.attrs['f_start'] = mode_list[0][0]
        dset.attrs['f_final'] = fcent
        dset.attrs['vna_pow'] = power
        dset.attrs['vna_span'] = fspan
        dset.attrs['vna_pts'] = npoints
        dset.attrs['vna_rbw'] = fspan / (npoints - 1)
        dset.attrs['vna_ifb'] = bandwidth
        dset.attrs['nmodes'] = mode_list.shape[0]
        dset.attrs['ato_voltage'] = setVoltage['x']
        dset.attrs['ato_freq'] = setFreq['x']
        dset.attrs['ato_step'] = step_size
        dset.attrs['beta'] = fit_dict['beta']
        dset.attrs['powerbeta'] = fit_dict['powerbeta']
    idx+=1
print("Closing connection to Stepper Motor ", anc.close())
print("ALL VALUES RECORDED.")


