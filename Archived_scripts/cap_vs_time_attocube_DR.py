__author__ = 'Aaron'

import time
import numpy as np
from attocube.attocube import ANC300
from pathlib import Path as p
from datetime import datetime
from pytz import timezone
import h5py

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']
anc = ANC300()

exp_name = 'cap_vs_time_warmup_DR'
filepath = p.home()/'Desktop'/'ORGAN_15GHz'/'ORGAN_DR_run_7_refl'
time_interval = 5*60 #(in seconds)
f= h5py.File(filepath / p(exp_name + '.hdf5'), 'a')
# cap = f.create_dataset('cap', data=np.array([]), compression='gzip', compression_opts=6, maxshape=(None,))
# dt = h5py.special_dtype(vlen=str)
# time_dset = f.create_dataset('time', data=[], compression='gzip', compression_opts=6, maxshape=(None,),dtype=dt)

for i in np.arange(12):
    cap = f['cap']
    time_dset = f['time']
    cap_meas = anc.cap['x']
    t = datetime.now(timezone('Australia/Perth')).strftime(fmt)
    print('The capacitance of the stage is: %f nF' %cap_meas)
    cap.resize(cap.shape[0]+1,axis=0)
    cap[-1:] = cap_meas
    time_dset.resize(time_dset.shape[0]+1,axis=0)
    time_dset[-1:] = str(t)
    time.sleep(time_interval)



