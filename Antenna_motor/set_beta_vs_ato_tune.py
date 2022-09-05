__author__ = 'Aaron Quiskamp'
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
target_beta = 1.5
beta_error_window = 0.1 # amount either side of target beta that is acceptable
beta_upper = target_beta + beta_error_window #max beta
beta_lower = target_beta - beta_error_window #min beta
step_size = 30 # how many steps per iteration
dip_prom = 3 # prominence in dB of the reflection dip
dip_width = 0 # number of points wide in freq
max_height = 10 # must be below this value to be considered (dB)
#############
ato_start = 0
ato_end = 5_000
ato_step = 50
total_steps = int((ato_end - ato_start) / ato_step) + 1
up_down = 'd'  # set to up, to set to down replace 'u' with 'd'
#############

# Folder To Save Files to:
exp_name = 'OQ_rt_sweep_beta_set'
filepath = p.home()/'Desktop'/'Aaron'/'Experiments'/'Antenna_motor'/exp_name

# fcentral, fspan, bandwidth, npoints, naverages, power
mode_list = np.array([[6_000_000_000,80_000_000,1500,3201,1,0]])

setVoltage = {'x':45,'y': 45} # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'x':500,'y': 500} # freq in

anc.freq(setFreq)
anc.V(setVoltage)
anc.ground()

vnass.set_module()  # Reset VNA Module
vnass.establish_connection_uphase()  # Establish connection to VNA

ato_pos_vals = np.arange(ato_start, ato_end + ato_step, ato_step)

# Attocube code begins
for idx, ato_pos in enumerate(tqdm(ato_pos_vals)):
    print(f'Moving to ato_pos:{ato_pos}')
    if ato_pos == 0 or idx == 0:  # since send a 0 instructs the stage to move continuously
        anc.ground()
    else:
        anc.step('x',ato_step,up_down)
        time.sleep(0.5)  # need to sleep
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
        print(f'Dip found at {f0/1e9} GHz')
        best_window = 0.03
        plot_freq_vs_db_mag_vs_phase(freq_data_GHz,db_data,uphase,f0[0])

        ######### fit to reflection dip
        fit_dict = test_refl_fit(ready_data,freq_data_GHz,dips[0],best_window,np.linspace(0,60,30),filepath)
        powerbeta = fit_dict['powerbeta']
        beta = fit_dict['beta']
        print(f'The current fitted beta={beta:.2f}, and the power_beta={powerbeta:.2f}')
        while (beta_lower>=beta) or (beta>=beta_upper):
            print(f'The current fitted beta={beta:.2f}, and the power_beta={powerbeta:.2f}')
            if beta<beta_lower:
                print(f'beta<{beta_lower} so move antenna in to achieve beta_target=[{beta_lower},{beta_upper}]')
                anc.step('y',step_size,'d')

            elif beta>beta_upper:
                print(f'beta>{beta_upper} so move antenna out to achieve beta_target=[{beta_lower},{beta_upper}]')
                anc.step('y', step_size, 'u')

            time.sleep(0.5) # let antenna settle
            #update mode params
            mode = [f0[0], 80e6, bandwidth, npoints, power, average]
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
        mode_list =np.array([[int(f0), 80_000_000, bandwidth, npoints, power, average]])
    ############ save data
    with h5py.File(filepath / p(exp_name + '.hdf5'), 'a') as f:
        dset = f.create_dataset(str(idx), data=ready_data, compression='gzip', compression_opts=6)  # VNA dset
        try:
            f['Freq']
        except:
            fdset = f.create_dataset('Freq', data=freq_data, compression='gzip', compression_opts=6)
            mode = [f0[0], 50e6, bandwidth, npoints, power, average]
            fdset.attrs['f_cent'] = mode[0]  # this is from the mode map / next freq
            fdset.attrs['vna_pow'] = mode[4]
            fdset.attrs['vna_span'] = mode[1]
            fdset.attrs['vna_pts'] = mode[3]
            fdset.attrs['vna_ave'] = mode[5]
            fdset.attrs['vna_rbw'] = mode[1] / (mode[3] - 1)
            fdset.attrs['vna_ifb'] = mode[2]
            fdset.attrs['ato_voltage'] = setVoltage['x']
            fdset.attrs['ato_freq'] = setFreq['x']
            fdset.attrs['ato_step'] = ato_step
            fdset.attrs['total_steps'] = total_steps
        dset.attrs['ato_pos'] = ato_pos
        dset.attrs['beta'] = fit_dict['beta']
        dset.attrs['powerbeta'] = fit_dict['powerbeta']
print("Closing connection to Stepper Motor ", anc.close())
print("ALL VALUES RECORDED.")


