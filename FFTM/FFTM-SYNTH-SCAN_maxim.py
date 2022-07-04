__author__ = 'Maxim'
import visa
import time
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.ticker as mtick
from matplotlib import cm
import warnings
warnings.filterwarnings("ignore")
import smtplib
import h5py

#Parameters
Fp = 1.94434197e9-250000#1.94434197e9-250000
Fs = Fp
P = 7+3

crosscorr = False            #CC?
psd = True     #PSD?
sensitivity = -35#41#-35
source = False
perturb = False

Fspan = 31        #span
FPspan = 0.85e6
BW = 1
Npts = 1601
Nstep = 101
Naver = 2*128                 #Number of Averages
notify = True               #send an email?
folder = "C:\\MeasurementData\\"
prefix = folder + "SF-narrow--extra+"+str(P)+"dBm-"
suffix = "FFTM"
temperature = False

Fs_vec = np.linspace(6e4,1e5,Npts)#(1,2e3,Npts)#(1,1000,Npts)#(Fs-Fspan/2,Fs+Fspan/2,Npts)
Fp_vec = np.linspace(Fp-FPspan/2,Fp+FPspan/2,Nstep)

def FFTread(ch1):
    AR = fftm.query("CALC"+(ch1)+":DATA?")
    #print(AR)
    fAR = [float(x) for x in AR.split(",")]
    #inst.write("INIT1")
    return fAR

rm = visa.ResourceManager()

print("Good morning, Maxim. It looks like you some stuff connected:")
print(rm.list_resources())
print("I am going to use the following devices:")
fftm = rm.open_resource('GPIB1::25::INSTR')

sg = rm.open_resource('GPIB1::19::INSTR')
print(sg.query("*IDN?"))
print(fftm.query("*IDN?"))

if perturb:
    sg.write("*rst; *cls")
#sg.write(":TRIG:SEQ:SOUR EXT")
#sg.write(":TRIG:EXT:SOUR TRIG1")
sg.write(":SOUR:FREQ:CW " + str(Fp_vec[0]))
sg.write(":SOUR:POW:LEV:IMM:AMPL " + str(P)+" dBm")
sg.write(":OUTP:STAT ON")
sg.write(":PULM:STAT OFF")
sg.write(":OUTP:MOD:STAT OFF")

if temperature:
    LAKE_gpib = "GPIB0::13::INSTR"
    LAKE_channel = "A"
    lake = rm.open_resource(LAKE_gpib)
    print(lake.query("*IDN?"))

#FFT Initialisation
fftm.write("*rst; status:preset; *cls")
#time.sleep(31)

fftm.write("SENS:FREQUENCY:STAR " + str(Fs_vec[0]))
fftm.write("SENS:FREQUENCY:STOP " + str(Fs_vec[-1]))
fftm.write("AVERAGE:COUN "+str(Naver))
fftm.write("AVERAGE ON")
fftm.write("CALIBRATION:AUTO OFF")
fftm.write("CALIBRATION:ZERO:AUTO OFF")
fftm.write("INP1:IMP 1MOHM")

fftm.write("SENS:SWE:POIN "+str(Npts))
fftm.write("SENS:AVER:TCON NORM")                       #Average method to "Normal"
fftm.write("SENS:WIND:TYPE HANN")                       #Main Window Hanning Window
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

if crosscorr:
    fftm.write("INP2:STATE ON")
    time.sleep(5)
    fftm.write("INP2:IMP 1MOHM")
    time.sleep(2)
    fftm.write("INP2:COUP AC")
    time.sleep(3)
    fftm.write("CALC1:FEED 'XFR:POW"+str_psd+" 1'")
    fftm.write("CALC2:FEED 'XFR:POW"+str_psd+" 2'")
    fftm.write("CALC3:FEED 'XFR:POW:CROS 2,1'")
    fftm.write("CALC1:FORM MLOG")
    fftm.write("CALC2:FORM MLOG")  # Meas Data LOG MAGNITUDE
    fftm.write("CALC3:FORM MLOG")                           #Meas Data LOG MAGNITUDE
    fftm.write("CALC1:UNIT:POW " + unit)  # Y axis Units dBvrms
    fftm.write("CALC2:UNIT:POW "+ unit)  # Y axis Units dBvrms
    fftm.write("CALC3:UNIT:POW dBVrms")  # Y axis Units dBvrms
    fftm.write("SENS:VOLT2:RANG:UNIT:VOLT dBVrms")
    fftm.write("SENS:VOLT2:RANG:UPP -35")  # Input Range
    fftm.write("CALC2:STAT ON")
    fftm.write("CALC3:STAT ON")
else:
    fftm.write("CALC1:FEED 'XFR:POW" + str_psd + " 1'")                #Meas Data PSD 1
    time.sleep(6)
    fftm.write("CALC1:FORM MLOG")                           #Meas Data LOG MAGNITUDE
    fftm.write("CALC1:UNIT:POW " + unit)                #Y axis Units dBvrms

if source:
    fftm.write("SOUR:FUNC:SHAP RAND")
    fftm.write("SOUR:VOLT:LEV:AMPL -10DBM")
    fftm.write("OUTP:STAT ON")


#fftm.write("SENS:BAND:RES 3")

#fftm.write("SENS:BAND:RESOLUTION:AUTO ON")

#BANDWIDTH?
fftm.write("CAL:ZERO:AUTO ONCE")
time.sleep(21)

ttime = float(fftm.query("SENS:SWE1:TIME:SPAN?"))  # Asks how long the data collection will take
Ttime = ttime*Naver + 7  # Works out total measurement time
print("One step is completed in "+str(Ttime/60)+'min. Total time: '+str(datetime.timedelta(seconds=Nstep*(Ttime+5)))+'. ')

#SA.write("INIT:IMM")
#time.sleep(Ttime)
Rx = np.zeros((Npts,len(Fp_vec)))
fftm.write("INIT:CONT ON")
if crosscorr:
    Qx = np.zeros((Npts,len(Fp_vec)))
    Cx = np.zeros((Npts,len(Fp_vec)))

plt.ion()
fig = plt.figure("FFTM DOWNLOAD")
plt.draw()

if temperature:
    temp = np.zeros(len(Fp_vec))

for ii in range(len(Fp_vec)):
    sg.write(":SOUR:FREQ:CW " + str(Fp_vec[ii]))
    time.sleep(5)
    fftm.write("SYST:KEY 21")  # Measurement restart
    time.sleep(Ttime)

    fftm.write("DISP:TRAC:Y:AUTO ONCE")  # Autoscales the Y-axis
    Rx[:, ii] = FFTread("1")
    if crosscorr:
        Qx[:, ii] = FFTread("2")
        Cx[:, ii] = FFTread("3")

    if temperature:
        temp[ii] = float(lake.query("KRDG? " + LAKE_channel))

    fig.clf()
    ax = fig.add_subplot(111)
    ax.plot(Fs_vec, Rx[:, ii], linewidth=2)
    plt.title('Measured step ' + str(ii) + " of " + str(len(Fp_vec)))
    ax.set_ylabel('PSD ')
    ax.set_xlabel('Frequency (Hz)')
    ax.xaxis.set_major_formatter(mtick.FormatStrFormatter('%2.2e'))
    plt.axis('tight')
    plt.pause(0.01)
    plt.draw()
    print("Measuring " + str(ii) + " of " + str(len(Fp_vec)))

if temperature:
    filename = prefix+"-magn-phas-freq-"+suffix + str(P)+"dBm-"+str(np.mean(temp))+"K.hdf5"
else:
    filename = prefix + "-magn-phas-freq-" + suffix + str(P) + "dBm.hdf5"
print("Saving to file: "+filename)
with h5py.File(filename, 'w') as f:
    channel1 = f.create_dataset('Magnitude', (Npts,len(Fp_vec)), dtype=np.float64, compression="gzip", compression_opts=9)
    if crosscorr:
        channel2 = f.create_dataset('Magnitude2', (Npts, len(Fp_vec)), dtype=np.float64, compression="gzip",
                                    compression_opts=9)
        channel3 = f.create_dataset('Magnitude3', (Npts, len(Fp_vec)), dtype=np.float64, compression="gzip",
                                    compression_opts=9)
    channel4 = f.create_dataset('Frequency', (len(Fs_vec),), dtype=np.float64, compression="gzip", compression_opts=9)
    channel5 = f.create_dataset('Sweep Frequency', (len(Fp_vec),), dtype=np.float64, compression="gzip", compression_opts=9)
    if temperature:
        channel6 = f.create_dataset('Temperature', (len(Fp_vec),), dtype=np.float64, compression="gzip",
                                    compression_opts=9)

    channel1[:,:] = Rx
    if crosscorr:
        channel2[:, :] = Qx
        channel3[:, :] = Cx
    channel4[:] = Fs_vec
    channel5[:] = Fp_vec
    if temperature:
        channel6[:] = temp

if notify:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login("notifications.running.scripts", "lno42helium3")
    msg = "Power Scan complited"
    server.sendmail("notifications.running.scripts@gmail.com", "maxim.goryachev@gmail.com", msg)
    server.quit()

if perturb:
    sg.write(":OUTP:STAT OFF")

fig.clf()
plt.ioff()
#print(len(y_data))
plt.plot(Fs_vec-Fs,Rx[:,-1], linewidth = 2)
#plt.title('Magnitude')
plt.ylabel('Magnitude, dB')
plt.xlabel('Frequency, Hz')
#plt.colorbar()
plt.show()

pmax = np.zeros(len(Fp_vec))
for ii in range(len(Fp_vec)):
    pmax[ii] = np.max(Rx[:,ii])

plt.plot(Fp_vec-Fp,pmax, linewidth = 2)
#plt.title('Magnitude')
plt.ylabel('Magnitude, dBm')
plt.xlabel('Pump Frequency, Hz')
#plt.colorbar()
plt.show()


if temperature:
    plt.plot(Fp_vec-Fp,temp, linewidth = 2)
    #plt.title('Magnitude')
    plt.ylabel('Temperature, K')
    plt.xlabel('Pump Frequency, Hz')
    #plt.colorbar()
    plt.show()

plt.contourf(Fp_vec-Fp, Fs_vec, Rx, 10, cmap=plt.cm.coolwarm,origin='lower')
plt.title('Signal Power')
plt.ylabel('Signal Frequency (Hz)')
plt.xlabel('Pump Frequency (Hz)')
plt.colorbar()
plt.show()

meanFFT = np.zeros(Npts)
maxFFT = np.zeros(len(Fp_vec))
for ii in range(len(Fp_vec)):
    meanFFT += Rx[:,ii]/len(Fp_vec)


RxBack = np.zeros(Rx.shape)

for ii in range(len(Fp_vec)):
    RxBack[:,ii] = Rx[:,ii]-meanFFT
    maxFFT[ii] = max(Rx[:,ii])#max(RxBack[:, ii])


plt.contourf(Fp_vec-Fp, Fs_vec, RxBack, 10, cmap=plt.cm.coolwarm,origin='lower')
plt.title('PSD')
plt.yscale('log')
plt.ylabel('Signal Frequency, Hz')
plt.xlabel('Pump Frequency, Hz')
plt.colorbar()
plt.show()

fftm.close()
sg.close()
if temperature:
    lake.close()