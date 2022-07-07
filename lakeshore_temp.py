__author__ = 'Nikita Kostylev'
__version__ = '20.03.2015_1.0'

# THIS SCRIPTS IS FOR BASIC CONNECTION TO LAKESHORE TO MEASURE TEMPERATURE
# Warning! No classes => only one lakeshore is allowed!

#import cryolib.lakeshore as lakeshore # For lakeshore 370
import cryolib.lakeshore340 as lakeshore

lake_inst = None  # Instance to store reference to lakeshore gpib object


# Connects to Lakeshore with default settings and stores lakeshore reference object
# inst: gpib resource object
def connect(lake_gpib, device_id, new_line_char='\r\n'):
    global lake_inst
    lake_inst = lakeshore.connect(lake_gpib, device_id, new_line_char)  # Connect to device
    lakeshore.reset(lake_inst)  # Reset device
    return


# Get temperature:
# channel(optional): channel number, eg "1", default value = "8"
#
# returns temp (float) in Kelvin
def get_temp(channel="8"):
    temp = lakeshore.get_temperature(lake_inst, channel)
    return temp

def get_resistance(channel="8"):
    temp = lakeshore.get_resistance(lake_inst, channel)
    return temp


# Terminates Connection to Lakeshore
def disconnect():
    lakeshore.terminate(lake_inst)
    return
