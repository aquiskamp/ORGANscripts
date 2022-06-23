__author__ = 'Aaron Quiskamp'
### just view vna output based on mode file
import matplotlib.pyplot as plt
import numpy as np
import time
import vna_single_sweep as vnass
import cryolib.general as gen
from Antenna_motor.coupling_functions import *

vnass.set_module()  # Reset VNA Module
vnass.establish_connection_uphase()  # Establish connection to VNA

#fcent,fspan,bandwidth,npoints,power,average
mode_params = np.array([[7160000000,60000000,300,1601,1,0]])

# Sweep over vna modes
for mode in mode_params:
    uphase,sweep_data = vnass.sweep_multi_trace(mode)  # Do a sweep with these parameters
    fcent,fspan,bandwidth,npoints,power,average = mode
    # Processing Starts here
    freq_data = gen.get_frequency_space(fcent, fspan, npoints)  # Generate list of frequencies
    freq_data_GHz = freq_data/1e9
    ready_data = np.transpose(sweep_data)  # Get a transposed version of sweep_data for saving
    db_data = gen.complex_to_dB(sweep_data)
    plot_freq_vs_db_mag_vs_phase(freq_data_GHz,db_data,uphase,fcent)
time.sleep(100)
print("ALL VALUES RECORDED. SWEEP COMPLETE.")

