import warnings
import os
import time
import numpy as np
import cryolib.general as gen
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from prettytable import PrettyTable
from attocube.attocube import ANC300
import vna_single_sweep as vnass
import lakeshore_temp as lakesm
from pathlib import Path as p
from datetime import datetime
from pytz import timezone

exp_name = 'script_test'
filepath = p.home()/p('Desktop/VNA/ORGANattocube')/exp_name
runfile = "run1.csv"

mode_list = np.loadtxt(filepath/runfile, dtype='f8,f8,f8,i,i,f8', delimiter=',')

if np.size(mode_list) == 1: # In case we have only one mode
    mode_list = np.asarray([mode_list])

for mode in mode_list:
    fcent = mode[0]
    fspan = mode[1]
    bandwidth = mode[2]
    npoints = int(mode[3])
    power = mode[4]
    print(mode)
    print(list(mode_list).index(mode))
    sweep_data =np.ones(1601)

    if list(mode_list).index(mode) == 0:
        ready_data = np.transpose(sweep_data)
    else:
        ready_data = np.append(ready_data,np.transpose(sweep_data)[:-1])

    print(ready_data.size)