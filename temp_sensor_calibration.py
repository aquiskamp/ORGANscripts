__author__ = 'Aaron'

import time
import lakeshore_temp as lakesm
from pathlib import Path as p

LAKE_gpib = "GPIB0::13::INSTR"
LAKE_device_id = "LSCI,MODEL340,342638,061407"
LAKE_channel_A = "A"
LAKE_channel_B = "B"
lakesm.connect(LAKE_gpib, LAKE_device_id)

save_file = p.home()/'Desktop'/'Aaron'/'Experiments'/'R2D2_temp_sensor_cal'/'A_vs_B_vs_temp.txt'
#file = open(save_file,'w')
#file.close()

wait_time = 30
fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']
#temp_meas = lakesm.get_temp(LAKE_channel)
while True:
    temp_meas_B = lakesm.get_temp(LAKE_channel_B)
    temp_meas_A = lakesm.get_temp(LAKE_channel_A)
    print(f'TEMP_A = {temp_meas_A:0.2f}K, TEMP_B = {temp_meas_B:0.2f}K')

    res_meas_B = lakesm.get_resistance(LAKE_channel_B)
    res_meas_A = lakesm.get_resistance(LAKE_channel_A)
    print(f'RES_A = {res_meas_A:0.2f} OHMS, RES_B = {res_meas_B:0.2f} OHMS')

    with open(save_file,'a') as f:
        f.write(str(temp_meas_A)+',')
        f.write(str(temp_meas_B)+',')
        f.write(str(res_meas_A)+',')
        f.write(str(res_meas_B))
        f.write('\n')

    time.sleep(wait_time)



