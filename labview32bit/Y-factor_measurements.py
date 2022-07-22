# script for Y-factor measurements
import numpy as np
import time
from pathlib import Path as p
from DAQ_scripts import DAQ_functions as df
import subprocess
from tqdm import tqdm

#=======================================================================================================================================
#Synthesizer settings
SYNTH_gpib = "GPIB4::19::INSTR"  # Full GPIB Address of SYNTH
synth_p = 12 #set power level (dbm) of sg
synth_fc = 16_000_000_000
synth = df.connect(SYNTH_gpib)
synth.write("*rst; *cls")  #device reset and clear status
synth.write(":OUTP:STAT ON") #turn on rf state
synth.write(":OUTP:MOD:STAT OFF") #turn off mod state
synth.write(":SOUR:POW:LEV:IMM:AMPL " + str(synth_p) + " dBm")  # set power level

digi_n_sweeps = 8
save_dir = p.home()/p('Desktop/ORGAN_15GHz/ORGAN_DR_run_9')
exp_name = 'short_cal_mag_rescan'
synth_lst = np.genfromtxt(save_dir/exp_name/'rescan_synth.txt')

for freq in tqdm(synth_lst):
    synth.write(":SOUR:FREQ:CW " + str(freq))  # set frequnecy to synth_fc.
    print('Setting synth to %s GHz' %(freq/1e9))
    subprocess.Popen(r"cd C:\Users\equslab\AppData\Local\Programs\Python\Python38-32& python Digitize_labview32.py " + '%s\%s_%i_Hz.h5'%(save_dir/exp_name,exp_name,freq), shell=True)
    time.sleep(17.179869184*digi_n_sweeps)