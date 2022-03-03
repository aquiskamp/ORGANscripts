__author__ = 'Aaron'

import time
import numpy as np
from attocube.attocube import ANC300
from pathlib import Path as p
from datetime import datetime
from pytz import timezone
import h5py
import lakeshore_temp as lakesm

LAKE_gpib = "GPIB0::13::INSTR"
LAKE_device_id = "LSCI,MODEL340,342638,061407"
LAKE_channel = "8"
lakesm.connect(LAKE_gpib, LAKE_device_id)

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']
anc = ANC300()

exp_name = 'cap_vs_time_cooldown_R2D2'
filepath = p.home()/'Desktop'/'ORGAN_15GHz'/exp_name
time_interval = 5*60 #(in seconds)
f= h5py.File(filepath / p(exp_name + '.hdf5'), 'w')
cap = f.create_dataset('cap', data=np.array([]), compression='gzip', compression_opts=6, maxshape=(None,))
dt = h5py.special_dtype(vlen=str)
time_dset = f.create_dataset('time', data=[], compression='gzip', compression_opts=6, maxshape=(None,),dtype=dt)
temp = f.create_dataset('temp', data=np.array([]), compression='gzip', compression_opts=6, maxshape=(None,))

for i in np.arange(120):
    cap_meas = anc.cap['x']
    t = datetime.now(timezone('Australia/Perth')).strftime(fmt)
    temp_meas = lakesm.get_temp(LAKE_channel)
    print('The capacitance of the stage is: %f nF, and the temp is: %f K' %(cap_meas,temp_meas))
    cap.resize(cap.shape[0]+1,axis=0)
    cap[-1:] = cap_meas
    time_dset.resize(time_dset.shape[0]+1,axis=0)
    time_dset[-1:] = str(t)
    temp.resize(temp.shape[0]+1,axis=0)
    temp[-1:] = temp_meas
    time.sleep(time_interval)

        # cap = anc.cap['x']
        # t = datetime.now(timezone('Australia/Perth')).strftime(fmt)
        # print('The current capicatnce of the stage is:',str(cap))
        # cap_file = open(str(filepath) + '_cap.txt', "a")  # saving to text file
        # time_file = open(str(filepath) + '_time.txt', "a")  # saving to text file
        # cap_file.write(str(cap) + '\n')
        # time_file.write(str(t) + '\n')



