import h5py

import gather_data as gd
import cryolib.general as gen
import numpy as np
import scipy.signal as sig
import Antenna_motor.coupling_functions as cf
from pathlib import Path as p

# ---reading VNA and presenting tings ----------
#params = gd.input_popup(False)
#ready_data, db_data, freq_data = gd.gather_data(params, True)
#gd.present_data(db_data, freq_data, params[0], params[1])



#-----reading file and fitting tings----------
#path = r"C:\Users\deepa\PycharmProjects\pythonProject\Deepali_single_sweep_010.hdf5"
path = r"C:\Users\deepa\OneDrive\Documents\2022\SEM 1\Research\data\rt_test\rt_test.hdf5"
#path = r"C:\Users\deepa\OneDrive\Documents\2022\SEM 1\Research\data\antenna_vs_freq\antenna_vs_freq.hdf5"
#------
with h5py.File(path, 'r') as f:  # file will be closed when we exit from WITH scope
    vna = f['0'][()]  # remember this is still complex
    vna_dataset = f['0']
    print("KEYS:", vna_dataset.attrs.keys())
    vna_transpose = np.transpose(vna)
    fcent = vna_dataset.attrs['f_final']
    fstart = vna_dataset.attrs['f_start']
    power = vna_dataset.attrs['vna_pow']
    fspan = vna_dataset.attrs['vna_span']
    npoints = vna_dataset.attrs['vna_pts']

    print(
        " Start Frequency (Hz) : %d \n Final Frequency (Hz) : %d \n VNA Span (Hz): %d \n No. Points: %d \n "
        " Power (dBm) : %d "
        % (fstart, fcent, fspan, npoints, power))
    full_freq = np.linspace(fcent - fspan // 2, fcent + fspan // 2, vna.shape[0])
    params = fstart, fcent, power, fspan, npoints

z_data= vna[:, 0] + vna[:, 1] * 1j
db_data = gen.complex_to_dB(vna_transpose)
mindb = db_data.argmin()
fr = full_freq[mindb]
dips = sig.find_peaks(-db_data, height= 18, prominence=2, width = 30)
gd.present_data(db_data,full_freq,fcent, fspan)
gd.fit_data(full_freq, z_data, db_data, fcent, fspan)

# # #-----
# #
# freq, vna, param  = gd.read_h5_file(path)  #vna_dataset is the original form
# #
# db_data = gen.complex_to_dB(vna)
# #
# z_data_raw = np.transpose(vna)
# z = z_data_raw[:, 0] + z_data_raw[:, 1] * 1j
# #
# gd.fit_data(freq,z, db_data, param[0], param[1])
# #



#gd.present_data(db_data, freq, param[0], param[1])




