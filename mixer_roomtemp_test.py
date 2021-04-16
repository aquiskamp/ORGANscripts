# test mixer for different mod freqs from synth

import numpy as np
import time
from pathlib import Path as p
import DAQ_functions as df
import subprocess

#=======================================================================================================================================
#Synthesizer settings
SYNTH_gpib = "GPIB0::19::INSTR"  # Full GPIB Address of SYNTH
synth_p = 13 #set power level (dbm) of sg
synth_fc = 16200000000
synth = df.connect(SYNTH_gpib)
synth.write("*rst; *cls")  #device reset and clear status
synth.write(":OUTP:STAT ON") #turn on rf state
synth.write(":OUTP:MOD:STAT OFF") #turn off mod state
synth.write(":SOUR:POW:LEV:IMM:AMPL " + str(synth_p) + " dBm")  # set power level
synth.write(":SOUR:FREQ:CW " + str(synth_fc))  # set frequnecy to synth_fc.

synth_lst = [16200000000]

for freq in synth_lst:
    synth.write(":SOUR:FREQ:CW " + str(freq))  # set frequnecy to synth_fc.
    time.sleep(2)
    subprocess.Popen(r"cd C:\Users\equslab\AppData\Local\Programs\Python\Python38-32& python Digitize_labview32.py " + str(freq), shell=True)
    time.sleep(17.179869184*11)