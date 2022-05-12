__author__ = 'Deepali Rajawat'

# dont forget to import things
from easygui import *
from prettytable import PrettyTable
import numpy as np
import vna_single_sweep as vnass
import cryolib.general as gen
from pathlib import Path as p
import h5py
from datetime import datetime
from pytz import timezone
import matplotlib.pyplot as plt
import Antenna_motor.coupling_functions as cf


# variables

# Generates popup box for user inputs
# Input Prompts: "Centre Frequency (Hz)", "Frequency Span (Hz)", "Bandwidth (Hz)",
# "No. Points", "No. Averages", "Power (dBm)"
def input_popup():
    text = "Enter the following details:"
    title = "VNA Sweep Parameters"
    input_list = ["Centre Frequency (Hz)", "Frequency Span (Hz)", "Bandwidth (Hz)", "No. Points", "No. Averages",
                  "Power (dBm)"]
    output = multenterbox(text, title, input_list)
    param = np.array(output)
    # message = "Entered details are in form of list :" + str(output)
    # msg = msgbox(message, title)

    dat_dtype = {
        'names': ('Fcent (Hz)', 'Fspan (Hz)', 'BW (Hz)', 'NPoints', 'NAverages', 'Power (dBm)'),
        'formats': ('f8', 'f8', 'f8', 'i', 'i', 'f8')}
    dat = np.zeros(7, dat_dtype)
    table_data = PrettyTable(dat.dtype.names)
    table_data.add_row(param)

    print("Loaded Settings:")
    print(table_data)

    return param


# Gathers data from VNA and writes to hdf5 file if specified
# returns sweep data and transpose of sweep data.

def gather_data(params, writefile):
    #    params = input_popup()                                                                                         #gather VNA sweep parameters
    channel = "1"  # VNA Channel number
    warn_email_list = ['22496421@student.uwa.edu.au']
    vnass.set_module(channel)                       #do i need channel?
    vnass.establish_connection()  # establish connection to vna

    sweep_data = vnass.sweep(params)  # Do a sweep with these parameters
    db_data = gen.complex_to_dB(sweep_data)
    ready_data = np.transpose(sweep_data)

    fcent, fspan, bandwidth, npoints, power, average = params
    freq_data = gen.get_frequency_space(fcent, fspan, npoints)

    # find actual resonant frequency and how far off initial sweep was
    dips, f0, dips_dict = cf.dipfinder(db_data, freq_data, p_width=30, prom=2, Height=20)  # get frequency of dip
    dip_difference = (abs(f0 - fcent) / fspan) * 100

   #if the difference is larger than 3%, resweep and reduce span to increase resolution
    if dip_difference > 3:

        params[0] = f0
        params[1] = int(fspan/2)                        #idk if you need to typecast

        sweep_data = vnass.sweep(params)  # Do a sweep with these parameters
        db_data = gen.complex_to_dB(sweep_data)
        ready_data = np.transpose(sweep_data)

    if writefile:
        t = datetime.now(timezone('Australia/Perth')).strftime("%Y_%m_%d %H_%M_%S")
        time_stamp = "time=%s" % t
        filepath = p.home()
        filename = "vna_antennacoupling" + fcent + "_" + time_stamp
        full_filename = p(filepath / (str(filename) + '.h5'))
        print(full_filename)

        with h5py.File(full_filename, 'w') as f:
            full_freq = np.linspace(fcent - fspan // 2, fcent + fspan // 2, ready_data.shape[0])  # freq list in Hz
            dset = f.create_dataset('VNA', data=ready_data, compression='gzip', compression_opts=6)  # VNA dset
            fdset = f.create_dataset('Freq', data=full_freq, compression='gzip', compression_opts=6)
            fdset.attrs['f_final'] = fcent
            fdset.attrs['vna_pow'] = power
            fdset.attrs['vna_span'] = fspan
            fdset.attrs['vna_pts'] = npoints
            fdset.attrs['vna_ave'] = average
            fdset.attrs['vna_rbw'] = fspan / (npoints - 1)
            fdset.attrs['vna_ifb'] = bandwidth
            # fdset.attrs['nmodes'] = mode_list.shape[0]
            fdset.attrs['time'] = t

        print('SWEEP FINISHED')

        return ready_data, db_data, freq_data


def print_h5_struct(name, obj):
    if isinstance(obj, h5py.Dataset):
        print('Dataset:', name)
    elif isinstance(obj, h5py.Group):
        print('Group:', name)

#reads
def read_h5_file(filename):
    with h5py.File(filename, 'r') as f:  # file will be closed when we exit from WITH scope
        f.visititems(print_h5_struct)  # print all strustures names
        freq = f['Freq'][()]
        vna = f['VNA'][()]  # remember this is still complex
        vna_transpose = np.transpose(vna)
        freq_dataset = f['Freq']
        fcent = freq_dataset.attrs['f_final']
        power = freq_dataset.attrs['vna_pow']
        fspan = freq_dataset.attrs['vna_span']
        npoints = freq_dataset.attrs['vna_pts']
        average = freq_dataset.attrs['vna_ave']
        bandwidth = freq_dataset.attrs['vna_ifb']
        print(
            "Centre Frequency (Hz) : %d \n Frequency Span (Hz): %d \n Bandwidth (Hz): %d \n No. Points: %d \n No. "
            "Averages : %d \n Power (dBm) : %d "
            % (fcent, fspan, bandwidth, npoints, average, power))
        params = fcent, fspan, bandwidth, npoints, average, power
    return freq, vna_transpose, params


# processes data and shows it in a graph. No function fitting or calculation of the coupling constant occurs in this
# function. Also finds how far the dip is from the centre of the graph. (necessary in later stages (func fitting)?)
def present_data(db_data, freq_data, fcent, fspan):
    plt.ion()  # makes graph interactive
    # fig = plt.figure("VNA")
    # fig.clf()

    plt.plot(freq_data, db_data)
    plt.ylabel('S11 (dB)')
    plt.xlabel('Frequency (GHz)')
    plt.title("f = %.3f GHz" % (fcent / 1e9), fontsize=16)


    dips, f0, dips_dict = cf.dipfinder(db_data, freq_data, p_width=30, prom=2, Height=20)  # get frequency of dip
    dip_difference = (abs(f0 - fcent) / fspan) * 100
    txt = "Dip frequency (GHz): %.3f\n Centre Frequency (GHz) : %.3f \n Percentage difference : %d%%\n" % (f0, fcent, dip_difference)
    print(txt)

    plt.text(10, 10, txt)
    plt.show()

def fit_data(f_data, z_data):
    port1 = circuit.reflection_port(f_data, z_data)
    port1.plotrawdata()
