from labview_class import LabView
lv = LabView()
'''It is a good idea to calibrate the fpga before use (both offset and scale calibration)
    -- Number of averages needs to be set on the host Vi (ie update rate) before starting script'''
import pyvisa as visa
import time
import numpy as np
#import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")
#import Cryo_switch as cs


#Heater powers to sweep through
Pstart = 0 #uW
Pend = 100 #uW
Pstep = 20 #uW

heater_R = 10e3 # heater resistance in ohms

P_list = np.arange(Pstart,Pend+Pstep,Pstep)#uW
V_list = np.sqrt(P_list*1e-6*heater_R) #Voltage to sweep through in Volts
print("Starting Y-factor measurments at "+time.ctime(time.time())+"\nHeater voltages are:")
print(V_list)
print(" ")

#fft measurment time
fcent = 30e6
npts = 6553
span = 1 #25MHz approx (uses sliding bar)
nspectra = 1 # how many spectrums to take

lv.simple_setup(fcent,npts,span,nspectra)

fft_wait_time = nspectra*3.0+10

#Heater wait times for temp to stabilise
temp_stab_time = 30*60 #sec

#file paths
#save_path = r'C:\Users\equslab\Desktop\test1.hdf5'
folder = "C:\\MeasurementData\\JPA_Y_factor_run0"
prefix = "\\Y_factor_no_switch2_"
extension = ".hdf5"



def fftread(save_path,wait=fft_wait_time):
    lv.save_data(True, save_path)  # set save directory
    try:
        lv.digitize()
    except:
        print(' ')
    time.sleep(wait)
    return

rm = visa.ResourceManager()

print("I am going to use the following devices:")
VSp = rm.open_resource("USB0::0x2A8D::0x1002::MY61002047::0::INSTR")

print(VSp.query("*IDN?"))



#VSp Initialisation
#time.sleep(20*60)
#print(time.ctime(time.time()))
VSp.write("VOLT 0.0,(@1)")
VSp.write("OUTP ON,(@1)")
time.sleep(10*60)
print('Starting at '+time.ctime(time.time()))


#Assumes switchs are already in calibration orientation
for i,h_v in enumerate(V_list):
    #Apply voltage and wait for temp to stabilise
    VSp.write("VOLT "+str(h_v)+",(@1)")
    if i>0:
        time.sleep(temp_stab_time)
    else:
        time.sleep(1)
    #take measurement
    fftread(folder + prefix + 'P=' + str(P_list[i]) + 'uW_' + 'T=' + str(time.time()) + extension)
    time.sleep(5)
    fftread(folder + prefix + 'P=' + str(P_list[i]) + 'uW_' + 'T=' + str(time.time()) + extension)
    time.sleep(5)
    fftread(folder + prefix + 'P=' + str(P_list[i]) + 'uW_' + 'T=' + str(time.time()) + extension)
    time.sleep(5)
    fftread(folder + prefix + 'P=' + str(P_list[i]) + 'uW_' + 'T=' + str(time.time()) + extension)
    print('Done '+str(i+1)+'/'+str(len(V_list)))

lv.save_data(True, folder + 'end' + extension)  # change save path so we don't overwrite exisiting data?
VSp.write("VOLT 0.0,(@1)")
VSp.write("OUTP OFF,(@1)")
print('Y factor done at: '+time.ctime(time.time()))


for i in range(int(24*6)):
    time.sleep(10*60)
    fftread(folder + prefix + 'timings_' + 'T=' + str(time.time()) + extension)
    time.sleep(10 * 60)

lv.save_data(False, folder + 'end' + extension)  # change save path so we don't overwrite exisiting data?
VSp.close()