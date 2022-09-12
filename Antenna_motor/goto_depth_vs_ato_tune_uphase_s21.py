__author__ = 'Aaron Quiskamp'
'''Goto antenna depth then take a s21 measurement of Q using a relay and then tune the rod'''
import time
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import argrelextrema
import vna_single_sweep as vnass
import cryolib.general as gen
from pathlib import Path as p
from coupling_functions import *
from attocube.attocube_usb import ANC300
import h5py
from tqdm import tqdm
from relays.two_port_relay import relay_on_off
import DVM.dvm as dvm
anc = ANC300()
dvm.connect() #connect to dvm
dvm_range = 100000
dvm_res = 1
dvm_error_window = 10 #move antenna to +- this value
f0_array = np.genfromtxt('f0_array.txt') #from previous run
dvm_array = np.genfromtxt('dvm_vals.txt') #from previous run

############# ANPz101 PARAMETERS
step_size = 5 # how many steps per iteration
dip_prom = 5 # prominence in dB of the reflection dip
dip_width = 0 # number of points wide in freq
max_height = 10 # must be below this value to be considered (dB)
############# # ANR240 PARAMETERS
ato_start = 0
ato_end = 4_000
ato_step = 30
total_steps = int((ato_end - ato_start) / ato_step) + 1
up_down = 'd'  # set to up, to set to down replace 'u' with 'd'
#############

# Folder To Save Files to:
exp_name = 'OQ_sweep_goto_dvm_s21'
filepath = p.home()/'Desktop'/'Aaron'/'Experiments'/'ORGAN_Q'/exp_name

#### Start position of mode
# fcentral, fspan, bandwith, npoints, naverages, power
mode = np.array([6_080_000_000,80_000_000,1500,3201,1,0])

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
    # put in reflection mode
    relay_on_off('close', '01')
    time.sleep(1)
    # Sweep over vna modes
    uphase,sweep_data = vnass.sweep_multi_trace(mode)  # Do a sweep with these parameters
    db_data = gen.complex_to_dB(sweep_data)
    ready_data = np.transpose(sweep_data)

    fcent,fspan,bandwidth,npoints,power,average = mode
    freq_data = gen.get_frequency_space(fcent, fspan, npoints)  # Generate list of frequencies
    freq_data_GHz = freq_data/1e9

    ######### dipfinder
    dips, f0, dips_dict = dipfinder(db_data,freq_data,p_width=dip_width, prom=dip_prom, Height=max_height)
    print(f'Dip found at {f0/1e9} GHz')
    plot_freq_vs_db_mag_vs_phase(freq_data_GHz, db_data, uphase, f0[0])

    ####### Go to dvm val now
    target_dvm = np.interp(f0, f0_array, dvm_array)
    dvm_lower = target_dvm - dvm_error_window
    dvm_upper = target_dvm + dvm_error_window
    dvm_val = dvm.read_4w_meas(dvm_range, dvm_res)  #current antenna stage position

    while (dvm_lower>=dvm_val) or (dvm_val>=dvm_upper):
        print(f'current dvm_val:{dvm_val:0.2f}')
        if dvm_val<dvm_lower:
            print(f'dvm_val<{dvm_lower} so move antenna out to achieve dvm_target=[{dvm_lower},{dvm_upper}]')
            anc.step('y',step_size,'u')

        elif dvm_val>dvm_upper:
            print(f'dvm_val>{dvm_upper} so move antenna in to achieve dvm_target=[{dvm_lower},{dvm_upper}]')
            anc.step('y', step_size, 'd')

        dvm_val = dvm.read_4w_meas(dvm_range, dvm_res)  #current antenna stage position

    print(f'dvm_val in range = [{dvm_lower},{dvm_upper}], SUCCESS!')

    # update mode params
    mode = [f0[0], fspan, bandwidth, npoints, power, average]
    uphase, sweep_data = vnass.sweep_multi_trace(mode)
    ready_data = np.transpose(sweep_data)  # Get a transposed version of sweep_data for saving
    db_data = gen.complex_to_dB(sweep_data)
    freq_data = gen.get_frequency_space(f0[0], fspan, npoints)  # Generate list of frequencies
    freq_data_GHz = freq_data / 1e9
    plot_freq_vs_db_mag_vs_phase(freq_data_GHz, db_data, uphase, f0[0])

    ####### Take S21 Q measurement now
    relay_on_off('open', '01') # put in transmission mode
    time.sleep(1)
    # Sweep over vna modes
    uphase, sweep_data_s21 = vnass.sweep_multi_trace(mode)  # Do a sweep with these parameters
    db_data_s21 = gen.complex_to_dB(sweep_data_s21)
    ready_data_s21 = np.transpose(sweep_data_s21)
    plot_freq_vs_db_mag(freq_data_GHz, db_data_s21, f0[0])

    ############ save data
    with h5py.File(filepath / p(exp_name + '.hdf5'), 'a') as f:
        S11 = f.create_dataset('S11_' + str(idx), data=ready_data, compression='gzip', compression_opts=6)  # VNA dset
        S21 = f.create_dataset('S21_' + str(idx), data=ready_data_s21, compression='gzip', compression_opts=6)  # VNA dset
        S11.attrs['f0'] = f0
        S11.attrs['ato_pos'] = ato_pos
        S11.attrs['dvm_val'] = dvm_val
        fdset = f.create_dataset('Freq_'+ str(idx), data=freq_data, compression='gzip', compression_opts=6)
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
print("Closing connection to Stepper Motor ", anc.close())
print("ALL VALUES RECORDED.")


