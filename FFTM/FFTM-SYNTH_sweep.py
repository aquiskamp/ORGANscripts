__author__ = 'Aaron'
import pyvisa
import time
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import warnings
import Antenna_motor.coupling_functions as cf
import h5py
from tqdm import tqdm,trange
from pathlib import Path as p
matplotlib.use('Qt5Agg')
warnings.filterwarnings("ignore")
rm = pyvisa.ResourceManager()
def FFTread(ch1):
    AR = fftm.query("CALC"+(ch1)+":DATA?")
    #print(AR)
    fAR = [float(x) for x in AR.split(",")]
    #inst.write("INIT1")
    return fAR

# Folder To Save Files to:
exp_name = '10db_short'
filepath = p.home()/'Desktop'/'Aaron'/'Experiments'/'thermal_noise_model'/exp_name

mode_f = np.arange(7e9,10e9,0.25e9)
psd = True     #PSD?

fft_start = 1e6
fft_end = 10e6
fft_points = 801
fftf_vec = np.linspace(fft_start,fft_end,fft_points)
fft_cent = fftf_vec[fft_points//2]
fft_ave = 256
ave_update_rate = fft_ave//16
sensitivity = -50
nsteps = 1
Rx = np.zeros((fft_points,nsteps))

#calibrate sweep time
cal_fft_time = 4 # seconds
cal_averages = 100 # averages for time above
sweep_time = cal_fft_time/cal_averages # for a single sweep

### synth
sg_power = 12 #dbm

#print(rm.list_resources())
print("I am going to use the following devices:")

fftm = rm.open_resource('GPIB3::19::INSTR')
sg = rm.open_resource('USB0::0x0957::0x1F01::MY61252954::0::INSTR')
#sg = rm.open_resource('GPIB2::19::INSTR')

print(sg.query("*IDN?"))
print(fftm.query("*IDN?"))

#FFT Initialisation
fftm.write("*rst; status:preset; *cls")
fftm.write("SENS:FREQUENCY:STAR " + str(fftf_vec[0]))
fftm.write("SENS:FREQUENCY:STOP " + str(fftf_vec[-1]))
fftm.write("AVERAGE:COUN "+str(fft_ave))
fftm.write("AVERAGE ON")
fftm.write("SENS:AVER:IRES ON")
fftm.write("SENS:AVER:IRES:RATE %s"%ave_update_rate)
fftm.write("CALIBRATION:AUTO OFF")
fftm.write("CALIBRATION:ZERO:AUTO OFF")
fftm.write("INP1:IMP 50OHM")

fftm.write("SENS:SWE:POIN "+str(fft_points))
fftm.write("SENS:AVER:TCON NORM")                       #Average method to "Normal"
fftm.write("SENS:WIND:TYPE UNIF")                       #Main Window Hanning Window
fftm.write("DISPLAY:WIND:TRACE:X:SCAL:SPACING LOG")
fftm.write("SENS:VOLT1:RANG:UNIT:VOLT dBVrms")
fftm.write("SENS:VOLT1:RANG:UPP "+str(sensitivity))                #Input Range
fftm.write("INP1:COUP AC")
fftm.write("CALC1:STAT ON")
#fftm.write("SENS:BAND:RES 0.01")

if psd:
    str_psd = ":PSD"
    unit = "dBVrms/rtHz"
else:
    str_psd = ""
    unit = "dBVrms"

fftm.write("CALC1:FEED 'XFR:POW" + str_psd + " 1'")                #Meas Data PSD 1
fftm.write("CALC1:FORM MLOG")                           #Meas Data LOG MAGNITUDE
fftm.write("CALC1:UNIT:POW " + unit)                #Y axis Units dBvrms

sg.write(":SOUR:POW:LEV:IMM:AMPL " + str(sg_power)+" dBm")
sg.write(":OUTP:STAT ON")
sg.write(":OUTP:MOD:STAT OFF")

fftm.write("CAL:ZERO:AUTO ONCE")
time.sleep(21)

Ttime = sweep_time*fft_ave + 5  # Works out total measurement time
print("One step is completed in "+ str(Ttime) +' sec')

fftm.write("INIT:CONT ON")

plt.ion()
fig = plt.figure("FFTM DOWNLOAD")
plt.draw()
cf.move_figure()

for idx, mode in enumerate(tqdm(mode_f)):
    sg_f = mode + fft_cent
    sg.write(":SOUR:FREQ:CW " + str(sg_f))
    for ii in range(nsteps):
        print("Measuring " + str(ii+1) + " of " + str(nsteps))
        fftm.write("SYST:KEY 21")  # Measurement restart
        time.sleep(Ttime)

        fftm.write("DISP:TRAC:Y:AUTO ONCE")  # Autoscales the Y-axis
        Rx[:, ii] = FFTread("1")

        fig.clf()
        ax = fig.add_subplot(111)
        ax.plot(fftf_vec, Rx[:, ii], linewidth=2)
        plt.title('Measured step ' + str(ii+1) + " of " + str(nsteps))
        ax.set_ylabel('PSD ')
        ax.set_xlabel('Frequency (Hz)')
        plt.axis('tight')
        plt.pause(0.01)
        plt.draw()

    Rx_ave = Rx.mean(axis=1) # take mean for all traces in nsteps

    with h5py.File(filepath / p(exp_name + '.hdf5'), 'a') as f:
        mag = f.create_dataset(str(idx), data=Rx_ave, dtype=np.float64, compression="gzip", compression_opts=6)
        mag.attrs['mode_f'] = mode
        mag.attrs['sg_f'] = sg_f
        try:
            f['Freq']
        except:
            freq = f.create_dataset('Freq', data=fftf_vec, dtype=np.float64, compression="gzip", compression_opts=6)
            freq.attrs['fft_start'] = fft_start
            freq.attrs['fft_end'] = fft_end
            freq.attrs['fft_points'] = fft_points
            freq.attrs['fft_cent'] = fft_cent
            freq.attrs['fft_ave'] = fft_ave
            freq.attrs['sensitivity'] = sensitivity
            freq.attrs['nsteps'] = nsteps
            freq.attrs['sg_power'] = sg_power
            freq.attrs['units'] = unit

fftm.close()
sg.close()
print("SWEEP FINISHED")