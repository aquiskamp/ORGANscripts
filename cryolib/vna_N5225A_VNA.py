__author__ = 'Nikita Kostylev'
__version__ = '20.03.2015_1.0'

# Module to communicate with VNA via GPIB/SCPI

# ---- GPIB Communications Settings of this instrument >>>>
VNA_gpib = "GPIB1::16::INSTR"
VNA_device_id = "Agilent Technologies,N5225A,MY57252028,A.10.47.06"

# <<<<<<


import pyvisa
import numpy as np

import warnings
warnings.filterwarnings('ignore', '.*VI_SUCCESS_MAX_CNT.*')


# Connect to vna and check ID
# VNA_gpib: eg. "GPIB0::16::INSTR"
# device_id: eg. "Agilent Technologies,N5225A,MY51451161,A.09.80.20"
# new_line_char: new line character for this device
#
# Returns gpib resource object or None if wrong device
def connect(VNA_gpib, device_id, new_line_char='\n'):
    rm = pyvisa.ResourceManager() # Open visa resource manager
    # rm.list_resources()   # print available gpib resource names

    inst = rm.open_resource(VNA_gpib)  # Connect to resource
    inst.read_termination = new_line_char    # Let pyvisa know the device's termination character

    resp = inst.query("*IDN?").rstrip(inst.read_termination) # Check device ID
    print("Connected to Device ID = " + resp)

    if resp != device_id:
        inst.close()
        inst = None
        raise ValueError("Incorrect Device ID")

    return inst


# Resets the VNA to default settings
# inst: gpib resource object
def reset(inst):
    inst.write("*RST")  # Full device reset
    inst.write("SYSTem:PRESet") # System default settings
    inst.write("FORMat ASCII")  # Make sure output is in ASCII
    return


# Autoscales Y-axes on VNA
# inst: gpib resource object
# window (optional): window number, eg "1", default value = "1"
# trace_num (optional): trace number, eg "1", default value = "1"
def autoscale(inst, window="1", trace_num="1"):
    inst.write("DISPlay:WINDow" + window + ":TRACe" + trace_num + ":Y:SCALe:AUTO")
    return



# Prepares VNA for Continuous Linear Sweep S21 Measurement
# inst: gpib resource object
# port(optional): port number, eg "1", default value = "1"
# channel(optional): channel number, eg "1", default value = "1"
# window (optional): window number, eg "1", default value = "1"
# trace_num (optional): trace number, eg "1", default value = "1"
# trace_name (optional): trace name, eg "My_Trace", default value = "Def_Meas"
def s21_set_mode(inst, channel="1", window="1", trace_num="1", trace_name = "Def_Meas", port="1"):
    if (trace_num == "1"):
        inst.write("DISPlay:WINDow" + window + ":TRACe1:DEL")   # Delete existing first trace on screen if we want to use it

    inst.write("CALCulate" +channel + ":PARameter:DEFine:EXT '" + trace_name + "',S21") # Set channel for s21 measurement

    inst.write("DISPlay:WINDow" + window + ":STATE ON") # Activate window
    inst.write("DISPlay:WINDow" + window + ":TRACe" + trace_num + ":FEED '" + trace_name + "'") # Assign trace to window
    inst.write("DISPlay:WINDow" + window + ":TRACe" + trace_num + ":SELect")    # Show Trace
    inst.write("DISPlay:WINDow" + window + ":TRACe" + trace_num + ":TITLe:DATA " + "'Remote Measurement S21'")  # Title Trace
    inst.write("DISPlay:WINDow" + window + ":TRACe" + trace_num + ":TITLe:STATe ON")    # Show Trace Title

    inst.write("SENSe" + channel + ":SWEep:SPEed NORMal")  # Sweep speed normal
    inst.write("SENSe" + channel + ":SWEep:MODE CONTinuous")   # Continuous sweep
    inst.write("SENSe" + channel + ":SWEep:TYPE LINear")   # Linear Sweep Type

    inst.write("SOURce" + channel + ":POWer" + port + ":ATTenuation:AUTO ON")
    inst.write("SOURce" + channel + ":POWer" + port + ":MODE AUTO")    # Enable Auto attenuation of source

    inst.write("CALCulate" + channel + ":PARameter:SELect '" + trace_name + "'")  # Start measurement of s21 on this channel
    inst.write("CALCulate" + channel + ":FORMat:UNIT MLOGarithmic, DBM")    # Make sure the measurement is in dBm

    # Set Status register to check sweep progress
    inst.write("STAT:QUES:INT:MEAS" + str(get_channel_int_register(channel)) + ":ENAB " +
               str(get_channel_int_weight(channel)))

    autoscale(inst, window, trace_num)  # Autoscale window to update view

    return



# Set source power
# inst: gpib resource object
# power: power in dBm, eg -10
# port(optional): port number, eg "1", default value = "1"
# channel(optional): channel number, eg "1", default value = "1"

def set_source_power(inst, power, channel="1", port="1"):
    inst.write("SOURce" + channel + ":POWer" + port + ":LEVel " + str(power))
    return


# Set IF Bandwidth
# inst: gpib resource object
# bandwidth: bandwidth in Hz, eg 1000
# channel(optional): channel number, eg "1", default value = "1"
def set_bandwidth(inst, bandwidth, channel="1"):
    inst.write("SENSe" + channel + ":BANDwidth:RESolution " + str(bandwidth))
    return


# Set Number of Points per span
# inst: gpib resource object
# npoints: number of points, eg 1601
# channel(optional): channel number, eg "1", default value = "1"
def set_point_number(inst, npoints, channel="1"):
    inst.write("SENSe" + channel + ":SWEep:POINts " + str(npoints))
    return


# Set Number of Averages per span
# inst: gpib resource object
# naverages: number of averages, eg 10 (between 1 and 65536, to disable averaging set to 1)
# channel(optional): channel number, eg "1", default value = "1"
# avetype(optional): averaging type: "point" (for multiple each point) or "sweep" (default, for multiple sweeps)
def set_averaging(inst, naverages, avetype="sweep", channel="1"):
    if avetype == "sweep":
        inst.write("SENSe" + channel + ":AVERage:MODE SWEEP")
    else:
        inst.write("SENSe" + channel + ":AVERage:MODE POINT")

    inst.write("SENSe" + channel + ":AVERage:COUNt " + str(int(naverages)))
    inst.write("SENSe" + channel + ":AVERage:CLEar")

    if int(naverages) > 1:
        inst.write("SENSe" + channel + ":AVERage:STATe ON")
    else:
        inst.write("SENSe" + channel + ":AVERage:STATe OFF")
    return

# Set Central Frequency of Sweep
# inst: gpib resource object
# fcent: central frequency in Hz, eg 12.5e9, for 12.5GHz
# channel(optional): channel number, eg "1", default value = "1"
def set_fcentral(inst, fcent, channel="1"):
    inst.write("SENSe" + channel + ":FREQuency:CENTer " + str(int(fcent)))
    return


# Set Span of Sweep
# inst: gpib resource object
# fspan: span in Hz, eg 0.5e9, for 0.5GHz
# channel(optional): channel number, eg "1", default value = "1"
def set_fspan(inst, fspan, channel="1"):
    inst.write("SENSe" + channel + ":FREQuency:SPAN " + str(int(fspan)))
    return


# Get sweep time:
# inst: gpib resource object
# channel(optional): channel number, eg "1", default value = "1"
#
# returns sweep_time (float) in seconds
def get_sweep_time(inst, channel="1"):
    sweep_time = float(inst.query("SENSe" + channel + ":SWEep:TIME?").rstrip(inst.read_termination))
    return sweep_time


# Does the analyzer have a notification?
# inst: gpib resource object
# channel(optional): channel number, eg "1", default value = "1"
#
# returns True if this channel is still running sweep, False otherwise
def is_not_ready(inst, channel="1"):
    resp = int(inst.query("STAT:QUES:INT:MEAS" + str(get_channel_int_register(channel)) +
                          ":COND?").rstrip(inst.read_termination))

    return (resp == get_channel_int_register(channel))


# Calculate Formatted Data (output in dB)
# inst: gpib resource object
# channel(optional): channel number, eg "1", default value = "1"
#
# returns numpy array (1xN) of amplitudes in dB
def download_formatted(inst, channel="1"):
    resp = inst.query("CALCulate" + channel + ":DATA? FDATA").rstrip(inst.read_termination)
    str_data = resp.split(',')
    fl_data = np.asarray([float(i) for i in str_data]) # Convert dB's to floats
    return fl_data


# Calculate Formatted Data (output in dB)
# inst: gpib resource object
# channel(optional): channel number, eg "1", default value = "1"
#
# returns numpy array (2xN)of amplitudes in dB
def download_complex(inst, channel="1"):
    resp = inst.query("CALCulate" + channel + ":DATA? SDATA").rstrip(inst.read_termination)
    str_data = resp.split(',')
    r_data = np.asarray([float(item) for i,item in enumerate(str_data) if (i % 2) == 0]) # Pick reals: every second item in list
    c_data = np.asarray([float(item) for i,item in enumerate(str_data) if ((i - 1) % 2) == 0]) # Pick complexes: every second+1 item in list
    return np.asarray([r_data, c_data])




# Close connection
# inst: gpib resource object
def terminate(inst):
    reset(inst)
    inst.close()
    return




# ___ LOCAL USE FUNCTIONS ____


# Mainly for local use: Get System Integrity Register
# channel: channel number
def get_channel_int_register(channel):
    ch = int(channel)
    if ((ch >= 1) and (ch <= 14)):
        register = 1
    elif ((ch >= 15) and (ch <= 28)):
        register =  2
    elif ((ch >= 29) and (ch <= 32)):
        register = 3
    else:
        register = 0
        raise ValueError("Incorrect Channel Number!")

    return register




# Mainly for local use: Get System Integrity Weight
# channel: channel number
def get_channel_int_weight(channel):
    ch = int(channel)
    dict = {1: 1, 2: 2, 15: 2, 29: 2, 3: 4, 16: 4, 30: 4, 4: 8, 17: 8, 31: 8, 5: 16, 18: 16, 32: 16, 6: 32, 19: 32,
            7: 64, 20: 64, 8: 128, 21: 128, 9: 256, 22: 256, 10: 512, 23: 512, 11: 1024, 24: 1024, 12: 2048, 25: 2048,
            13: 4096, 26: 4096, 14: 8192, 27: 8192, 28: 16384}

    weight = dict.get(ch, 0)
    if (weight == 0):
        raise ValueError("Incorrect Channel Number!")

    return weight