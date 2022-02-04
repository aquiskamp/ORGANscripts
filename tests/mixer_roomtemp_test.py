# test mixer for different mod freqs from synth

import numpy as np
import time
from pathlib import Path as p
import DAQ_functions as df
import subprocess

#=======================================================================================================================================
Synthesizer settings
SYNTH_gpib = "GPIB1::19::INSTR"  # Full GPIB Address of SYNTH
synth_p = 12 #set power level (dbm) of sg
synth_fc = 16100000000
synth = df.connect(SYNTH_gpib)
synth.write("*rst; *cls")  #device reset and clear status
synth.write(":OUTP:STAT ON") #turn on rf state
synth.write(":OUTP:MOD:STAT OFF") #turn off mod state
synth.write(":SOUR:POW:LEV:IMM:AMPL " + str(synth_p) + " dBm")  # set power level
#synth.write(":SOUR:FREQ:CW " + str(synth_fc))  # set frequnecy to synth_fc.

synth_lst = [9_040_000_000]
digi_n_sweeps = 5
save_dir = p.home()/p('Desktop/ORGAN_15GHz/MIXER_DIGI_TESTS/Sapphire_9GHz')
exp_name = 'IQ0618_'

for freq in synth_lst:
    #synth.write(":SOUR:FREQ:CW " + str(freq))  # set frequnecy to synth_fc.
    subprocess.Popen(r"cd C:\Users\equslab\AppData\Local\Programs\Python\Python38-32& python Digitize_labview32.py " + '%s\%s_%s_Hz.h5'%(save_dir,exp_name,freq), shell=True)
    time.sleep(17.179869184*digi_n_sweeps)