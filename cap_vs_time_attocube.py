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

exp_name = 'cap_vs_time_cooldown_R2D2'
filepath = p.home()/'Desktop'/'ORGAN_15GHz'/exp_name
time_interval = 5*60 #(in seconds)
# f = h5py.File(filepath / p(exp_name + '.hdf5'), 'w')
# dset =  f.create_dataset('capicatance', data=[], compression='gzip', compression_opts=6, maxshape=(None,))
idx = 0
while idx < 144:
    cap = anc.cap['x']
    t = datetime.now(timezone('Australia/Perth')).strftime(fmt)
    print('The current capicatnce of the stage is:',str(cap))
    cap_file = open(str(filepath) + '_cap.txt', "a")  # saving to text file
    time_file = open(str(filepath) + '_time.txt', "a")  # saving to text file
    cap_file.write(str(cap) + '\n')
    time_file.write(str(t) + '\n')

    # cap = anc.cap['x']
    # t = datetime.now(timezone('Australia/Perth')).strftime(fmt)
    # print('The current capicatnce of the stage is:',str(cap))
    # data = [(str(cap),str(t))]
    # print(data)
    # dset.resize(dset.shape[0] + len(data), axis=0)
    # dset[-len(data):] = data
    #
    time.sleep(time_interval)
    idx+=1
    print(idx)




