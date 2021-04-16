import win32com.client as win32
from pathlib import Path as p


vi_file = r'C:\Users\equslab\Desktop\Axion v3 - dev - test\Axion v3 - dev\Axion_v5.0(HOST)_hdf5_timed.vi' #path to VI
save_dir = str(p.home()/'Desktop/DAQ_test.hdf5')


digi_fc = 7000000
digi_span = 10000000
digi_points = 26214
digi_ave = 8192
#igi_startf = digi_fc - digi_span//2
#digi_stopf = digi_fc + digi_span//2
#digi_step = digi_span/digi_points
digi_n_sweeps = 2
wait_time = (17.179869184)*digi_n_sweeps*1000 # time before abort command is sent (in ms)

# Launch labview and the VI
LabVIEW = win32.dynamic.Dispatch('LabVIEW.Application')  # need dynamic so its "late-bound oriented"
VI = LabVIEW.getvireference(vi_file) #create VI reference
VI._FlagAsMethod("Call")  # Flag "Call" as Method

# set Digitzier params
VI.setcontrolvalue('Centre freq', str(digi_fc))  # Set centre freq for digitizer
VI.setcontrolvalue('N', str(2))
VI.setcontrolvalue('speed', -4)
VI.setcontrolvalue('wait', str(wait_time))
VI.setcontrolvalue('points', str(digi_points))
VI.setcontrolvalue('Window select', str(0))

# hdf5 save file
VI.setcontrolvalue('File path', save_dir)
VI.setcontrolvalue('Dataset Path', 'FFT')
VI.setcontrolvalue('Number of points', digi_points)

try:
    VI.Call()
except:
    print('Digitizer finished')

VI = None  # remove reference
