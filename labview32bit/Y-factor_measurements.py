# script for Y-factor measurements
import numpy as np
import time
from pathlib import Path as p
#from DAQ_scripts import DAQ_functions as df
from tqdm import tqdm
from labview_class import LabView
import pyvisa
rm = pyvisa.ResourceManager()
lv = LabView()

save_dir = p.home()/p('Desktop/Aaron/Experiments/thermal_noise_model')
exp_name = 'LNC_1_12_4k_yfactor_3'
synth_lst = np.genfromtxt(save_dir/exp_name/'synth_list.csv',delimiter='/n')
temp = 12.9

#=======================================================================================================================================
#Synthesizer settings
SYNTH_gpib = "USB0::0x0957::0x1F01::MY53270526::0::INSTR"  # Full GPIB Address of SYNTH
synth_p = 12 #set power level (dbm) of sg
synth = rm.open_resource(SYNTH_gpib)
synth.write("*rst; *cls")  #device reset and clear status
synth.write(":OUTP:STAT ON") #turn on rf state
synth.write(":OUTP:MOD:STAT OFF") #turn off mod state
synth.write(":SOUR:POW:LEV:IMM:AMPL " + str(synth_p) + " dBm")  # set power level
#=======================================================================================================================================
#Digitizer settings
fcent = 34.1e6
npts = 6553
span = 5 #25MHz approx (uses sliding bar)
nspectra = 20 # how many spectrums to take
lv.simple_setup(fcent,npts,span,nspectra)
#=======================================================================================================================================

for freq in tqdm(synth_lst):
    synth.write(":SOUR:FREQ:CW " + str(freq))  # set frequnecy to synth_fc.
    print('Setting synth to %s GHz' %(freq/1e9))
    save_path = str(save_dir / exp_name / ('temp_'+ str(temp) + '_' + 'LO_' + str(freq/1e9) + 'GHz.hdf5'))
    lv.save_data(True, save_path)  # set save directory
    try:
        lv.digitize()
    except:
        print('Digitizer Finished')
