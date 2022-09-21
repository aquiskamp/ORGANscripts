import h5py
import skrf

import gather_data as gd
import cryolib.general as gen
import numpy as np
import os
from path import Path
import scipy.signal as sig
import Antenna_motor.coupling_functions as cf
from pathlib import Path as p
import skrf as rf
import matplotlib.pyplot as plt

# # ---reading VNA and presenting tings ----------
# params = gd.input_popup(True)
# ready_data, db_data, z_data, freq_data = gd.gather_data(params, True)
# fitresults = gd.fit_data(freq_data, z_data, db_data, params[0], params[1])


#--- put filenames in array --------
#homepath = 'C:/Users/deepa/OneDrive/Documents/2022/SEM 1/Research/data/22aug'
#homepath2 = 'C:/Users/deepa/OneDrive/Documents/2022/SEM 1/Research/data/oscillations'
#homepath2 = 'C:/Users/deepa/OneDrive/Documents/2022/SEM 1/Research/data/29aug'
#homepath2 = 'C:/Users/deepa/OneDrive/Documents/2022/SEM 1/Research/data/6sept'
#homepath2 = 'C:/Users/deepa/OneDrive/Documents/2022/SEM 1/Research/data/6sept_largerlinearsweep711'
homepath2 = 'C:/Users/deepa/OneDrive/Documents/2022/SEM 1/Research/data/9sept_biglinearsweep'

lookingatoscillations = os.listdir(homepath2)
#all_files_and_folders = os.listdir(homepath)

#--- sort via time------
filelist = []
for file in lookingatoscillations:
    filelist.append(homepath2 + '/' + file)

sortedfiles = sorted(filelist, key = os.path.getmtime)



#-----reading file and fitting tings----------
#path = r"C:\Users\deepa\PycharmProjects\pythonProject\Deepali_single_sweep_010.hdf5"
#path = r"C:\Users\deepa\OneDrive\Documents\2022\SEM 1\Research\data\rt_test\rt_test.hdf5"
#path = r"C:\Users\deepa\OneDrive\Documents\2022\SEM 1\Research\data\vna_antennacoupling7130000000_time=2022_07_15 15_57_01.h5"
#path = r"C:\Users\deepa\OneDrive\Documents\2022\SEM 1\Research\data\vna_antennacoupling7130000000_time=2022_07_15 16_24_40.h5"


#path = r"C:\Users\deepa\OneDrive\Documents\2022\SEM 1\Research\data\antenna_vs_freq\antenna_vs_freq.hdf5"
#------
# with h5py.File(path, 'r') as f:  # file will be closed when we exit from WITH scope
#     vna = f['0'][()]  # remember this is still complex
#     vna_dataset = f['0']
#     print("KEYS:", vna_dataset.attrs.keys())
#     vna_transpose = np.transpose(vna)
#     fcent = vna_dataset.attrs['f_final']
#     fstart = vna_dataset.attrs['f_start']
#     power = vna_dataset.attrs['vna_pow']
#     fspan = vna_dataset.attrs['vna_span']
#     npoints = vna_dataset.attrs['vna_pts']
#
#     print(
#         " Start Frequency (Hz) : %d \n Final Frequency (Hz) : %d \n VNA Span (Hz): %d \n No. Points: %d \n "
#         " Power (dBm) : %d "
#         % (fstart, fcent, fspan, npoints, power))
#     full_freq = np.linspace(fcent - fspan // 2, fcent + fspan // 2, vna.shape[0])
#     params = fstart, fcent, power, fspan, npoints
#
# z_data= vna[:, 0] + vna[:, 1] * 1j
# db_data = gen.complex_to_dB(vna_transpose)
# mindb = db_data.argmin()
# fr = full_freq[mindb]
# dips = sig.find_peaks(-db_data, height= 18, prominence=2, width = 30)
# gd.present_data(db_data,full_freq,fcent, fspan)
# gd.fit_data(full_freq, z_data, db_data, fcent, fspan)
# gd.plotunwrappedphase(full_freq, z_data, fcent)

#---- to see smith chart for rtf test
# n = rf.Network(name = "test", s = z_data)
# fig2 = n.plot_s_smith(draw_labels=True)



#-----
#
qarr = []
chiarr = []
i = 0
for path in sortedfiles:
   # path = homepath2 + '/' + path
    freq, vna, param  = gd.read_h5_file(path)  #vna_dataset is the original form
    db_data = gen.complex_to_dB(vna)
    z_data_raw = np.transpose(vna)
    z = z_data_raw[:, 0] + z_data_raw[:, 1] * 1j
    i += 1
    print('iteration', i)
    if 0 <= i <= 200:
        #gd.find_desired_span(db_data, freq, param[0], z)
        #gd.plotunwrappedphase(freq,z,param[0], param[1], iteration=i)
        #gd.present_data(db_data,freq,param[0],param[1])
        fitresults = gd.fit_data(freq,z,db_data,param[0],param[1])
        qarr.append(fitresults['Ql'])
        chiarr.append(fitresults['chi_square'])




# os.chdir('C:/Users/deepa/OneDrive/Documents/2022/SEM 1/Research/data/9sept_biglinearsweep')
# filename = 'res_coupling_depth7129993355.135_time=2022_09_05 19_05_05.h5'
# #
# antennadepth, resfreq, couplingconstants, contrast, steparr = \
#     gd.read_summary(filename)
#
# fig, ax1 = plt.subplots()
# ax1.set_title('Coupling constant relative to antenna depth')
# color = 'tab:red'
# ax1.set_xlabel('Antenna Depth (mm)')
# ax1.set_ylabel('Coupling Constant', color=color)
# ax1.plot(antennadepth, betaarr, color=color)
# ax1.tick_params(axis='x', labelcolor=color)
#gd.fit_data(freq,z, db_data, param[0], param[1])
#gd.plotunwrappedphase(freq, z)


# #
#
# ------------------------------
# freq, vna, param = gd.read_h5_file(path)  #vna_dataset is the original form
#
# db_data = gen.complex_to_dB(vna)
#
# z_data_raw = np.transpose(vna)
# z = z_data_raw[:, 0] + z_data_raw[:, 1] * 1j
# gd.present_data(db_data, freq, 7160000000, 100000000)




