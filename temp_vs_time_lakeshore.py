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
LAKE_channel = "A"
lakesm.connect(LAKE_gpib, LAKE_device_id)

wait_time = 300
fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']
#temp_meas = lakesm.get_temp(LAKE_channel)
while True:
    temp_meas = lakesm.get_temp(LAKE_channel)
    print(f'The current temperature is {temp_meas:0.2f}K')
    time.sleep(wait_time)



