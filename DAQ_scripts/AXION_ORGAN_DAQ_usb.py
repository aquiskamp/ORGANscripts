__author__ = 'Aaron Quiskamp'

#Brief overview
#Step 1. Find mode. Do this using previous mode map data.
#Step 2. Fit to the TM010 mode. Find Q, linewidth, f_cent.
#Step 3. Send f_cent data to synth to mix down to FFT frequency
#Step 4. Take FFT, record metadata (B, phys_temp, etc) and save trace.
#Step 5. Step motor and repeat.

import warnings
import time
from datetime import datetime
from pytz import timezone
import numpy as np
import cryolib.general as gen
import lakeshore_temp as lakesm
from lmfit.models import PolynomialModel
import matplotlib.pyplot as plt
import subprocess
import h5py
from pathlib import Path as p
import vna_single_sweep as vnass
from attocube.attocube import ANC300
import DAQ_functions as df

fmt = "%Y_%m_%d__%H_%M_%S"
tz = ['Australia/Perth']
filepath = p.home()/p('Desktop/ORGAN_15GHz/ORGAN_DR_run_9/ORGAN_4K_run_1a')
measure_temp = False  # Do we actually want to measure Temperature here (Connect to Lakeshore via GPIB)?
temperature = 4
#=======================================================================================================================================

#Attocube ANR300
anc = df.connect_usb("ASRL3::INSTR")
up_down = 'd' # set to up. To set to down replace 'u' with 'd'
setVoltage = 60 # Voltage in Volts
setFreq = 1000 # Freq in Hz
anc.write("setv 1 "+str(setVoltage))
anc.write("setf 1 "+str(setFreq))

# #Mode map
model_freq = np.genfromtxt(filepath/'model_freq_2.csv',delimiter=',')
model_phi = np.genfromtxt(filepath/'model_phi_2.csv',delimiter=',')
tm010_model = PolynomialModel(4)
y = model_phi.flatten()
x = model_freq.flatten()
pars = tm010_model.guess(y, x=x)
mode_map = tm010_model.fit(y, pars, x=x)
final_fit = mode_map.best_fit
# mode_map.plot()
# plt.show()

#VNA settings
channel = "1" #VNA Channel Number
warn_email_list = ['21727308@student.uwa.edu.au']
vnass.set_module(channel, warn_email_list) # Reset VNA Module
vnass.establish_connection()    # Establish connection to VNA
sweep_type = "15.7--16.2GHz"

#Initial VNA Sweep
vna_fc = 15_945_671_875
vna_span = 50_000_000
vna_ifb = 300
vna_pts = 3201
vna_ave = 1
vna_pow = -10

#Synthesizer settings
SYNTH_gpib = "GPIB2::19::INSTR"  # Full GPIB Address of SYNTH
synth_p = 12 #set power level (dbm) of sg
synth_fc = 16000000000
synth = df.connect(SYNTH_gpib)
synth.write("*rst; *cls")  #device reset and clear status
synth.write(":OUTP:STAT OFF") #turn off rf state
synth.write(":OUTP:MOD:STAT OFF") #turn off mod state
synth.write(":SOUR:POW:LEV:IMM:AMPL " + str(synth_p) + " dBm")  # set power level
synth.write(":SOUR:FREQ:CW " + str(synth_fc))  # set frequnecy to synth_fc

#Lakeshore Temp settings (not really needed on this run)
LAKE_gpib = "GPIB1::13::INSTR"
LAKE_device_id = "LSCI,MODEL340,342638,061407"
LAKE_channel = "8"

digi_fc = 45_100_000 #MHz must match digitize_labview_32.py script
digi_points = 26214 #doesn't really matter
digi_ave = 8192 #doesn't matter
digi_n_sweeps = 242 #must match script!!
wait_time = (17.179869184)*digi_n_sweeps # time before abort command is sent (in sec)

#sweep VNA
params = [vna_fc, vna_span, vna_ifb, vna_pts, vna_ave, vna_pow]  # sweep parameters
vna_sweep_data = vnass.sweep(params)  # data points

#peakfinder settings
pheight_db = [-50] # update every sweep?
prom = 5

ato_step = 0 #start step
max_ato_step = 200 #max step, ie don't allow an unreasonable next scan steps
ato_list = np.array([18])

if measure_temp:
    print("Preparing Lakeshore for active Temperature Measurement")
    lakesm.connect(LAKE_gpib, LAKE_device_id)  # Prepare lakeshore if actively measuring temperature
#=======================================================================================================================================

# While Loop that runs as long as next ato step is less than max_ato_step
while ato_step < max_ato_step:
#=======================================================================================================================================
    #Step motor
    print("Stepping motor by " + str(ato_step) + " steps")
    if ato_step == 0: # since send a 0 instructs the stage to move continuously
        anc.stop()
        anc.ground()
    else:
        anc.step('x', ato_step, up_down)
        vna_fc = next_vna_fc
        ato_list = np.append(ato_list,ato_step + ato_list[-1])
#=======================================================================================================================================
    #Sweep
    vna_span = 50_000_000
    vna_ifb = 300
    vna_pts = 3201
    vna_ave = 1
    vna_pow = -10
    vna_rbw = vna_span / (vna_pts - 1)


    #sweep VNA
    print('Sweeping VNA')
    # turn VNA off
    vnass.power_on_off('ON')
    params = [vna_fc, vna_span, vna_ifb, vna_pts, vna_ave, vna_pow]  # sweep parameters
    vna_sweep_data = vnass.sweep(params)  # data points
    vna_freq_points = gen.get_frequency_space(vna_fc, vna_span, vna_pts)  # Generate list of frequencies
    vna_ready_data = np.transpose(vna_sweep_data)

    # Fit to the data
    mag_data = np.sqrt(vna_ready_data[:, 0] ** 2 + vna_ready_data[:, 1] ** 2)
    mag_data_db = 20 * np.log10(mag_data)

    #dynamically change peakheight
    peakheight = pheight_db[0] - 8

    #3db data to input as guess for fit
    f0, w3db, Q3db, peak_height, pheight_db = df.peakfinder(mag_data_db,vna_freq_points, prom, peakheight)
    #peakheight = pheight_db -10 # set peak height threshold for next pos in loop
    print('f0: %f GHz, 3dB width: %f MHz, Q_3dB: %.0f, peak_dB: %.1f' %(f0[0]/1e9, w3db[0]/1e6, Q3db[0], pheight_db[0]))
    if measure_temp:
        temperature = lakesm.get_temp(LAKE_channel)

    # file name
    t = datetime.now(timezone('Australia/Perth')).strftime(fmt)
    time_stamp = "time=%s" % t
    temp_stamp = "temp=" + str(temperature)
    fcent_stamp = "fcent=" + str(int(vna_fc)) #freq vna is set to (from mode map)
    fspan_stamp = "fspan=" + str(int(vna_span))
    npoints_stamp = "npoints=" + str(vna_pts)
    ato_pos_stamp = "atp_pos=" + str(ato_list[-1])

    filename = sweep_type
    filename += "_" + time_stamp
    filename += "_" + fcent_stamp
    filename += "_" + ato_pos_stamp

    full_filename = p(filepath / (str(filename) + '.h5'))

    #Q-fit with 3 linwdwidths of data
    Qfit, linewidth, fit_peak_db, fc_fit= df.Q_fit(mag_data**2, vna_freq_points, 1, f0[0],w3db[0], peak_height[0], True, True, filepath,filename+'.pdf') #use 3 linewdiths to fit to data (approx 9dB contrast)

    if up_down == 'u':
        next_vna_fc = df.roundup(f0[0] - 0.25*linewidth, vna_rbw)
    else:
        next_vna_fc = df.roundup(f0[0] + 0.25*linewidth, vna_rbw)
    next_ato_pos = int(round(abs(mode_map.eval(x = next_vna_fc) - mode_map.eval(x = f0[0]))))
    ato_step = int(next_ato_pos)
    print('f_c: ' + str(f0[0]) + ',lw: ' + str(int(linewidth)) + ', Next f_c: ' + str(int(next_vna_fc)) + ', Next ato_step: ' + str(ato_step) + ', Next pheight_db: ' +str(peakheight))

    #turn VNA off
    vnass.power_on_off('OFF')
    time.sleep(1)
#=======================================================================================================================================
    # Send fc - offset to Synthesizer for IF signal to be digitized
    synth.write(":OUTP:STAT ON") #turn on rf state
    synth_fc = f0[0] - digi_fc
    synth.write(":SOUR:FREQ:CW " + str(int(synth_fc))) #set frequnecy to synth_fc

#=======================================================================================================================================
    # write vna sweep to hdf5 file
    with h5py.File(full_filename, 'w') as f:
        dset = f.create_dataset('VNA', (vna_pts, 2), dtype=np.float64, compression='gzip', compression_opts=6)  # VNA dset
        dset[:, :] = vna_ready_data
        dset.attrs['vna_fc'] = vna_fc  # this is from the mode map / next freq
        dset.attrs['f0'] = f0  # this is from peakfinder
        dset.attrs['fc_fit'] = fc_fit  # this is from the fit
        dset.attrs['vna_pow'] = vna_pow
        dset.attrs['vna_span'] = vna_span
        dset.attrs['vna_pts'] = vna_pts
        dset.attrs['vna_ave'] = vna_ave
        dset.attrs['vna_rbw'] = vna_rbw
        dset.attrs['vna_ifb'] = vna_ifb
        dset.attrs['ato_step'] = ato_step
        dset.attrs['ato_pos'] = ato_list[-1]
        dset.attrs['Q3db'] = Q3db
        dset.attrs['Qfit'] = Qfit
        dset.attrs['fit_peak_db'] = fit_peak_db
        dset.attrs['linewidth'] = linewidth
        dset.attrs['temp'] = temperature
        dset.attrs['time'] = t
        dset.attrs['synth_fc'] = synth_fc
        dset.attrs['synth_pow'] = synth_p
        dset.attrs['integration_time'] = wait_time

#=======================================================================================================================================
    subprocess.Popen(r"cd C:\Users\equslab\AppData\Local\Programs\Python\Python38-32& python Digitize_labview32.py " + str(full_filename),shell=True)
    print('Integrating for %.2f mins' %(wait_time/60)) #convert to mins)
    time.sleep(wait_time)
    synth.write(":OUTP:STAT OFF")  # turn off rf state so VNA trace can be taken.
    time.sleep(1)

#retun to top

if measure_temp:
    lakesm.disconnect() # Disconnect from Lakeshore if actively measured temperature
synth.close()
anc.close()
#=======================================================================================================================================

