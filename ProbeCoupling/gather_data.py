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

#variables

#Generates popup box for user inputs
def input_popup():

    text = "Enter the following details:"
    title = "VNA Sweep Parameters"
    input_list = ["Centre Frequency (Hz)", "Frequency Span (Hz)", "Bandwidth (Hz)", "No. Points", "No. Averages", "Power (dBm)"]
    output = multenterbox(text, title, input_list)
    param = np.array(output)
   # message = "Entered details are in form of list :" + str(output)
    #msg = msgbox(message, title)

    dat_dtype = {
        'names': ('Fcent (Hz)', 'Fspan (Hz)', 'BW (Hz)', 'NPoints', 'NAverages', 'Power (dBm)'),
        'formats': ('f8', 'f8', 'f8', 'i', 'i', 'f8')}
    dat = np.zeros(7, dat_dtype)
    table_data = PrettyTable(dat.dtype.names)
    table_data.add_row(param)

    print("Loaded Settings:")
    print(table_data)

    return param


#Gathers data from VNA and writes to hdf5 file if specified

def gather_data(params, writefile):
#    params = input_popup()                                     #gather VNA sweep parameters
    channel = "1"                                               #VNA Channel number
    warn_email_list = ['22496421@student.uwa.edu.au']
    vnass.set_module(channel)
    vnass.establish_connection()                                #establish connection to vna

    sweep_data = vnass.sweep(params)                            # Do a sweep with these parameters
    db_data = gen.complex_to_dB(sweep_data)
    ready_data = np.transpose(sweep_data)

    fcent,fspan,bandwidth,npoints,power,average = params

    if writefile == True:

        t = datetime.now(timezone('Australia/Perth')).strftime(fmt)
        time_stamp = "time=%s" % t
        filepath = p.home()
        filename ="vna_antennacoupling" + fcent + "_" + time_stamp
        full_filename = p(filepath / (str(filename) + '.h5'))
        print(full_filename)

        with h5py.File(full_filename, 'w') as f:

            full_freq = np.linspace(fcent - fspan // 2, fcent + fspan // 2,ready_data.shape[0])  # freq list in Hz
            dset = f.create_dataset('VNA', data=ready_data, compression='gzip', compression_opts=6)  # VNA dset
            fdset = f.create_dataset('Freq', data=full_freq, compression='gzip', compression_opts=6)














