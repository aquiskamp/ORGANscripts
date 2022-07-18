__author__ = 'Aaron'
'Measure DVM vs time/temp'
import time
import numpy as np
import DVM.dvm as dvm
import lakeshore_temp as lakesm
from pathlib import Path as p
from datetime import datetime
from pytz import timezone

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']

temp_target = 5
time_step = 5*60

# Folder To Save Files to:
exp_name = 'rod_continuity_cooldown'
filepath = p.home()/'Desktop'/'Aaron'/'Experiments'/'ORGAN_Q'/exp_name
save_file = filepath/'resistance_vs_temp.txt'

# Static Temperature:
measure_temp = True  # Do we actually want to measure Temperature here (Connect to Lakeshore via GPIB)?
temperature = 20e-3  # (Kelvin) Manual Temperature Record (For No Lakeshore Access)

# Temperature Controller Settings
LAKE_gpib = "GPIB0::13::INSTR"
LAKE_device_id = "LSCI,MODEL340,342638,061407"
LAKE_channel = "8"

dvm.connect() #connect to dvm
dvm_range = 1_000
dvm_res = 1
dvm_val = dvm.read_2w_meas(dvm_range, dvm_res)  # stage position
dvm_list = np.array([])

if measure_temp:
    print("Preparing Lakeshore for active Temperature Measurement")
    lakesm.connect(LAKE_gpib, LAKE_device_id)  # Prepare lakeshore if actively measuring temperature
    temp = lakesm.get_temp(LAKE_channel)
    print(f'Current temp is {temp}K')

while temp>temp_target:
    dvm_val = dvm.read_2w_meas(dvm_range,dvm_res) #stage position
    temp = lakesm.get_temp(LAKE_channel)
    print(f'Current temp is {temp}K')
    print(f'Current resistance is {dvm_val}')
    t = datetime.now(timezone('Australia/Perth')).strftime(fmt)
    with open(save_file,'a') as f:
        f.write(str(temp)+',')
        f.write(str(dvm_val)+',')
        f.write(str(t))
        f.write('\n')
    time.sleep(time_step)

if measure_temp:
    lakesm.disconnect()  # Disconnect from Lakeshore if actively measured temperature

print("Closing connection to Stepper Motor ", dvm.close())
print("ALL VALUES RECORDED. SWEEP COMPLETE.")
