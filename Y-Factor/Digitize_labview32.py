#run 32 bit labview using python32 bit
import win32com.client as win32
from pathlib import Path as p
import time

filepath = p.home()/p('Desktop/ORGAN_15GHz/testing_mixer_roomtemp')
full_filename = filepath/'test.h5'
#Digitizer settings
vi_file = r'C:\Users\equslab\Desktop\Axion v3 - dev - test\Axion v3 - dev\Axion_v5.0(HOST)_hdf5_timed.vi'

digi_fc = 50000000
digi_points = 26214
digi_n_sweeps = 5
wait_time = (17.179869184)*digi_n_sweeps*1000 # time before abort command is sent (in ms)

#Launch labview and the VI
LabVIEW = win32.dynamic.Dispatch('LabVIEW.Application') #need dynamic so its "late-bound oriented"
VI = LabVIEW.getvireference(vi_file)
VI._FlagAsMethod("Call")  # Flag "Call" as Method

# set Digitzier params
VI.setcontrolvalue('Centre freq', str(digi_fc))  # Set centre freq for digitizer
VI.setcontrolvalue('N',str(2)) #set span
VI.setcontrolvalue('speed',-1) #set update rate
VI.setcontrolvalue('wait', str(wait_time))
VI.setcontrolvalue('points', str(digi_points))
VI.setcontrolvalue('Window select', str(0))

# hdf5 save file
VI.setcontrolvalue('File path', str(full_filename))
VI.setcontrolvalue('Dataset Path', 'FFT')
VI.setcontrolvalue('Number of points', digi_points)
##
try:
    VI.Call()
except:
    print('Digitizer finished')

VI = None  # remove reference
