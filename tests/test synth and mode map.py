import pyvisa
def connect(gpib):
    # rm.list_resources()   # print available gpib resource names
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(gpib)  # Connect to resource
    resp = inst.query("*IDN?").rstrip("\n") # Check device ID
    print("Connected to Device ID = " + resp)
    return inst

def connect_usb(usb):
    # rm.list_resources()   # print available gpib resource names
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(usb)  # Connect to resource
    print("Connected to Device ID = " + usb)
    return inst

#import vna_single_sweep as vnass
rm = pyvisa.ResourceManager()
print(rm.list_resources())
#vna = rm.open_resource('ASRL4::INSTR')
#vna.write("*RST")
# synth_fc = 16000000000
# vna.query("*IDN?")
# synth.write(":OUTP:STAT OFF") #turn on rf state
# synth.write(":OUTP:MOD:STAT OFF") #turn off mod state
# synth.write(":SOUR:FREQ:CW " + str(synth_fc))  # set frequnecy to synth_fc
# ato = connect_usb("ASRL4::INSTR")
# up_down = 'u' # set to up. To set to down replace 'u' with 'd'
# setVoltage = 30 # Voltage in Volts
# setFreq = 500 # Freq in Hz
# ato.write("setv 1 "+str(setVoltage))
# ato.write("setf 1 "+str(setFreq))
#
# channel = "1" #VNA Channel Number
# warn_email_list = ['21727308@student.uwa.edu.au']
# vnass.set_module(channel, warn_email_list) # Reset VNA Modul1e
# vnass.establish_connection()    # Establish connection to VNA
# sweep_type = "test_DAQ"



ato = rm.open_resource("ASRL1::INSTR")
up_down = 'u' # set to up. To set to down replace 'u' with 'd'
setVoltage = 5 # Voltage in Volts
setFreq = 1000 # Freq in Hz
ato.write("setv 1 "+str(setVoltage))
ato.write("setf 1 "+str(setFreq))
ato.write('setm 1 stp')
#
# filepath = p.home()/p('Desktop/ORGAN_15GHz/ORGAN_DR_run_9/ORGAN_4K_run_1a')
#
# # #Mode map
# model = load_modelresult(filepath/'tm010_model.sav')
# tm010_model = PolynomialModel(6)
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
# SYNTH_gpib = "GPIB0::11::INSTR"  # Full GPIB Address of SYNTH
# synth_p = 12 #set power level (dbm) of sg
# synth_fc = 15000000000
# synth = connect(SYNTH_gpib)
# synth.write("*rst; *cls")  #device reset and clear status
# synth.write(":OUTP:STAT ON") #turn on rf state
# synth.write(":OUTP:MOD:STAT OFF") #turn off mod state
# synth.write(":SOUR:POW:LEV:IMM:AMPL " + str(synth_p) + " dBm")  # set power level
# synth.write(":SOUR:FREQ:CW " + str(synth_fc))  # set frequnecy to synth_fc

3
