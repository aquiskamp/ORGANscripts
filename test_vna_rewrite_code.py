
import warnings
import os
import time
import numpy as np
import cryolib.general as gen
import matplotlib
import matplotlib.pyplot as plt
from prettytable import PrettyTable
from attocube.attocube import ANC300
import vna_single_sweep as vnass
import lakeshore_temp as lakesm
from pathlib import Path as p
from datetime import datetime
from pytz import timezone
import h5py

import warnings
VNA_gpib = "GPIB0::10::INSTR"  # Full GPIB Address of VNA
VNA_device_id = "Agilent Technologies,N5230A,MY45001201,A.07.50.67"  # VNA ID String
channel = '1'

warn_email_list = ['21727308@student.uwa.edu.au']
vnass.set_module(channel, warn_email_list) # Reset VNA Module
vnass.establish_connection()    # Establish connection to VNA
vnass.power_on_off('OFF')
time.sleep(2)
vnass.power_on_off('ON')