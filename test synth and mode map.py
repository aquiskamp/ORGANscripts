##from pathlib import Path as p
##import lmfit
##import numpy as np
##from lmfit.model import load_modelresult
##from lmfit.models import PolynomialModel
##import matplotlib
##import matplotlib.pyplot as plt
##import matplotlib.ticker as mtick
##import time
import pyvisa
##import DAQ_functions as df
#import vna_single_sweep as vnass
rm = pyvisa.ResourceManager()
print(rm.list_resources())
#vna = rm.open_resource('ASRL4::INSTR')
#vna.write("*RST")
# synth_fc = 16000000000
#vna.query("*IDN?")
# synth.write(":OUTP:STAT OFF") #turn on rf state
# synth.write(":OUTP:MOD:STAT OFF") #turn off mod state
# synth.write(":SOUR:FREQ:CW " + str(synth_fc))  # set frequnecy to synth_fc
# ato = df.connect_usb("ASRL3::INSTR")
# up_down = 'u' # set to up. To set to down replace 'u' with 'd'
# setVoltage = 30 # Voltage in Volts
# setFreq = 1000 # Freq in Hz
# ato.write("setv 1 "+str(setVoltage))
# ato.write("setf 1 "+str(setFreq))
#
# channel = "1" #VNA Channel Number
# warn_email_list = ['21727308@student.uwa.edu.au']
# vnass.set_module(channel, warn_email_list) # Reset VNA Module
# vnass.establish_connection()    # Establish connection to VNA
# sweep_type = "test_DAQ"



# ato = rm.open_resource("ASRL3::INSTR")
# up_down = 'u' # set to up. To set to down replace 'u' with 'd'
# setVoltage = 50 # Voltage in Volts
# setFreq = 1000 # Freq in Hz
# ato.write("setv 1 "+str(setVoltage))
# ato.write("setf 1 "+str(setFreq))

#filepath = p.home()/p('Desktop/ORGAN_15GHz/test_rt_DAQ')
#==================================================================================================
#Mode map
# model_freq = np.genfromtxt(filepath/'model_freq.csv',delimiter=',')
# model_phi = np.genfromtxt(filepath/'model_phi.csv',delimiter=',')
# tm010_model = PolynomialModel(6)
# y = model_phi.flatten()
# x = model_freq.flatten()
# pars = tm010_model.guess(y, x=x)
# fit_pars = tm010_model.fit(y, pars, x=x)
# final_fit = fit_pars.best_fit
# SYNTH_gpib = "GPIB2::19::INSTR"  # Full GPIB Address of SYNTH
# synth_p = 10 #set power level (dbm) of sg
# synth_fc = 16000000000
# synth = df.connect(SYNTH_gpib)
# synth.write("*rst; *cls")  #device reset and clear status
# synth.write(":OUTP:STAT ON") #turn on rf state
# synth.write(":OUTP:MOD:STAT OFF") #turn off mod state
# synth.write(":SOUR:POW:LEV:IMM:AMPL " + str(synth_p) + " dBm")  # set power level
# synth.write(":SOUR:FREQ:CW " + str(synth_fc))  # set frequnecy to synth_fc


