__author__ = 'Nikita Kostylev'
__version__ = '20.03.2015_1.0'

# Module to communicate with Lakeshore 370 Resistance Bridge via GPIB/SCPI



import pyvisa

import warnings
warnings.filterwarnings('ignore', '.*VI_SUCCESS_MAX_CNT.*')

# Connect to lakeshore and check ID
# lake_gpib: eg. "GPIB1::11::INSTR"
# device_id: eg. "LSCI,MODEL370,370732,04102008"
# new_line_char: new line character for this device
#
# Returns gpib resource object or None if wrong device
def connect(lake_gpib, device_id, new_line_char='\r\n'):
    rm = pyvisa.ResourceManager() # Open visa resource manager
    # rm.list_resources()   # print available gpib resource names

    inst = rm.open_resource(lake_gpib)  # Connect to resource
    inst.read_termination = new_line_char    # Let pyvisa know the device's termination character

    resp = inst.query("*IDN?").rstrip(inst.read_termination) # Check device ID
    print("Connected to Device ID = " + resp)

    if resp != device_id:
        inst.close()
        inst = None
        raise ValueError("Incorrect Device ID")

    return inst


# Resets the Lakeshore to default settings
# inst: gpib resource object
def reset(inst):
    inst.write("*RST")  # Full device reset
    return


# Get temperature:
# inst: gpib resource object
# channel(optional): channel number, eg "1", default value = "8"
#
# returns temp (float) in Kelvin
def get_temperature(inst, channel="6"):
    temp = float(inst.query("RDGK?" + channel).rstrip(inst.read_termination)) # For lakeshore 370
    return temp


# Terminates Connection to Lakeshore
# inst: gpib resource object
def terminate(inst):
    reset(inst)
    inst.close()
    return





