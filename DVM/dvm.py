import numpy as np
import pyvisa
import time
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")

dvm_address = 'USB0::0x0957::0x0607::MY47011729::0::INSTR'
rm = pyvisa.ResourceManager()

def connect():
    global dvm
    dvm = rm.open_resource(dvm_address)
    print(dvm.query('*IDN?'))
    dvm.write('*RST; *CLS')
    return dvm

def setup_4w_meas(range):
    dvm.write(f'MEASure:FRESistance? {range}')

def read_4w_meas(range,res):
    return float(dvm.query(f'MEAS:FRES? {range},{res}'))

def read_2w_meas(range,res):
    return float(dvm.query(f'MEAS:RES? {range},{res}'))

def close():
    dvm.close()


