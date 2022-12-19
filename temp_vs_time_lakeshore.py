__author__ = 'Aaron'

import time
import lakeshore_temp as lakesm
import pyvisa
rm = pyvisa.ResourceManager()
print(rm.list_resources())

LAKE_gpib = "GPIB2::13::INSTR"
LAKE_device_id = "LSCI,MODEL340,342638,061407"
#LAKE_device_id = "LSCI,MODEL370,370A7T,04102008"
LAKE_channel_A = "A"
LAKE_channel_B = "B"
#LAKE_channel_C = '5'
lakesm.connect(LAKE_gpib, LAKE_device_id)


wait_time = 300
fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']
#temp_meas = lakesm.get_temp(LAKE_channel)
while True:
    temp_meas_B = lakesm.get_temp(LAKE_channel_B)
    temp_meas_A = lakesm.get_temp(LAKE_channel_A)
    #temp_meas_C = lakesm.get_temp(LAKE_channel_C)
    #print(f'TEMP_A = {temp_meas_A:0.2f}K, TEMP_B = {temp_meas_B:0.2f}K, TEMP_C = {temp_meas_C:0.2f}K')
    print(f'TEMP_A = {temp_meas_A:0.2f}K, TEMP_B = {temp_meas_B:0.2f}K')
    time.sleep(wait_time)



