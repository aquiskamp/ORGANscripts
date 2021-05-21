#This script moves the stage in one direction then waits a set amount of time and then moves again. Good for when
#cold and don't want to warm the fridge 
import warnings
import os
import time
import pyvisa

ato_pos_start = 0
ato_pos_end = 400000 #ie 360deg
ato_pos_step = 600 #at roomtemp, 60V and f=1000Hz, step ~ 0.01deg
up_down = 'd' # set to up, to set to down replace 'u' with 'd'

setVoltage = 50 # key-value pair, x is axis, '60' is voltage Volts
setFreq = 500 # freq in Hz

rm = pyvisa.ResourceManager()

inst = rm.open_resource('TCPIP0::130.95.156.244::7230::SOCKET')
inst.write("setv 1 "+str(setVoltage))
inst.write("setf 1 "+str(setFreq))


# inst.write('setm 1 stp')
# time.sleep(0.5)
# inst.write('stepu 1 500')
# time.sleep(2)
# #inst.write('setm 1 gnd')
# time.sleep(0.5)
#print(inst.write('getv 1'))
##
### Starting Scan:
##ato_pos_vals = np.arange(ato_pos_start, ato_pos_end + ato_pos_step, ato_pos_step)
##
##print("Running Sweep over Phi = [" + str(ato_pos_start) + ", " + str(ato_pos_end) + "], with step = " +
##      str(ato_pos_step) + " (" + str(len(ato_pos_vals)) + " sweeps)")
##
### Run over step (phi) values
### Attocube code begins
##for ato_pos in ato_pos_vals:
##    print("Set position to ato_pos = " + str(ato_pos*0.01) + " " + "Degrees")
##    
##    if ato_pos == 0: #since send a 0 instructs the stage to move continuously 
##        inst.write("stop")
##        
##    else:
##        inst.write("setm 1 stp")
##        inst.write("step"+up_down + " " + "1" + " "+str(ato_pos - ato_pos_step*(list(ato_pos_vals).index(ato_pos)-1)))
##        time.sleep(2)# need to sleep otherwise grounds instantly 
##        inst.write("setm 1 gnd")
##        time.sleep(150)
    

