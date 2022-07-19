__author__ = 'Aaron Quiskamp'

#CHECK LIST FOR AXION_ORGAN_DAQ scipt.
#1)Make sure filepath is correct
#2)Check direction of stage
#3)Set encoder True or False and set noise_cal_offset
#4)Can uncomment mode_map csv to check that this is working and inside filepath dir
#5)SET default scan time (referenced to beta=1)
#6)SET inital VNA sweep (f_cent where mode is)
#7)SET GPIB for synth and VNA
#8)SET cal_wait_time for noise calibrations
#9)SET p_height and prominence for find_peaks based on mode
#10)ADJUST VNA settings
#11)SET how many linewidths each step should be

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
import pandas as pd
from attocube.attocube import ANC300
import DAQ_functions as df
from attocube.ANC350 import Positioner
from scipy import interpolate

anc = ANC300()

fmt = "%Y_%m_%d__%H_%M_%S"
tz = ['Australia/Perth']
filepath = p.home()/p('Desktop/ORGAN_15GHz/ORGAN_4K_run_1a_rescan')
measure_temp = False  # Do we actually want to measure Temperature here (Connect to Lakeshore via GPIB)?
use_encoder = False
temperature = 4
current_position = 0
noise_cal_offset = 30_000_000 #30MHz
#=======================================================================================================================================

#Attocube ANR300
up_down = 'd' # set to up, to set to down replace 'u' with 'd'
setVoltage = {'x': 60} # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'x': 1000} # freq in Hz
anc.V = setVoltage #This sets the voltage for the sweep.
anc.freq = setFreq #This sets the frequency for the sweep.

if use_encoder:
    anc350 = Positioner()
    initial_position = anc350.getPosition(axis['y'])
    print('Connected to', anc350.getActuatorName(axis['y']))
    print('Current Position', initial_position)

# #Mode map
model_freq = np.genfromtxt(filepath/'model_freq.csv',delimiter=',')
model_phi = np.genfromtxt(filepath/'model_phi.csv',delimiter=',')
tm010_model = PolynomialModel(4)
y = model_phi.flatten()
x = model_freq.flatten()
pars = tm010_model.guess(y, x=x)
mode_map = tm010_model.fit(y, pars, x=x)
final_fit = mode_map.best_fit

#beta map for dynamic scan rate
beta_df = pd.read_csv(filepath / 'freq_vs_beta_2.csv', delimiter=',')
beta_freq_function = interpolate.interp1d(beta_df['fr']*1e9, beta_df['beta'])
default_scan_time = (17.179869184)*180 # default scan time using beta=1
#VNA settings
channel = "1" #VNA Channel Number
warn_email_list = ['21727308@student.uwa.edu.au']
vnass.set_module(channel, warn_email_list) # Reset VNA Module
vnass.establish_connection()    # Establish connection to VNA
sweep_type = "nibble3"

#Initial VNA Sweep
vna_fc = 16_200_000_000
vna_span = 100_000_000
vna_ifb = 1000
vna_pts = 3201
vna_ave = 1
vna_pow = -10

#Synthesizer settings
SYNTH_gpib = "GPIB0::19::INSTR"  # Full GPIB Address of SYNTH
synth_p = 12 #set power level (dbm) of sg
synth_fc = 16000000000
synth = df.connect(SYNTH_gpib)
#synth.write("*rst; *cls")  #device reset and clear status
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
digi_n_sweeps = 210 #must match script!!
wait_time = (17.179869184)*digi_n_sweeps # time before abort command is sent (in sec)

cal_wait_time = (17.179869184)*8 # time before abort command is sent (in sec)

#sweep VNA
params = [vna_fc, vna_span, vna_ifb, vna_pts, vna_ave, vna_pow]  # sweep parameters
vna_sweep_data = vnass.sweep(params)  # data points

#peakfinder settings
pheight_db = [-40] # update every sweep?
prom = 6

ato_step = 0 #start step
max_ato_step = 50 #max step, ie don't allow an unreasonable next scan steps
ato_list = np.array([0]) # starting position

if measure_temp:
    print("Preparing Lakeshore for active Temperature Measurement")
    lakesm.connect(LAKE_gpib, LAKE_device_id)  # Prepare lakeshore if actively measuring temperature
#=======================================================================================================================================

# While Loop that runs as long as next ato step is less than max_ato_step
while ato_step < max_ato_step:
#=======================================================================================================================================
    #Step motor
    print(f"Stepping motor by {ato_step} steps")
    if ato_step == 0: # since send a 0 instructs the stage to move continuously
        anc.stop()
        anc.ground()
    else:
        anc.step('x', ato_step, up_down)
        vna_fc = next_vna_fc
        ato_list = np.append(ato_list,ato_step + ato_list[-1])
    if use_encoder:
        current_position = anc350.getPosition(axis['y'])
#=======================================================================================================================================
    #Sweep
    vna_span = 50_000_000
    vna_ifb = 300
    vna_pts = 6401
    vna_ave = 1
    vna_pow = -10
    vna_rbw = vna_span / (vna_pts - 1)

    #sweep VNA
    print('Sweeping VNA')
    # turn VNA on
    vnass.power_on_off('ON')
    params = [vna_fc, vna_span, vna_ifb, vna_pts, vna_ave, vna_pow]  # sweep parameters
    vna_sweep_data = vnass.sweep(params)  # data points
    vna_freq_points = gen.get_frequency_space(vna_fc, vna_span, vna_pts)  # Generate list of frequencies
    vna_ready_data = np.transpose(vna_sweep_data)

    # Fit to the data
    mag_data = np.sqrt(vna_ready_data[:, 0] ** 2 + vna_ready_data[:, 1] ** 2)
    mag_data_db = 20 * np.log10(mag_data)

    #dynamically change peakheight
    peakheight = pheight_db[0] - 5

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
    f0_stamp = "f0=" + str(int(f0[0])) #freq vna is set to (from mode map)
    fspan_stamp = "fspan=" + str(int(vna_span))
    npoints_stamp = "npoints=" + str(vna_pts)
    ato_pos_stamp = "atp_pos=" + str(ato_list[-1])
    ato_deg_stamp = "atp_deg=" + str(current_position)

    filename = sweep_type
    filename += "_" + time_stamp
    filename += "_" + fcent_stamp
    filename += "_" + f0_stamp
    filename += "_" + ato_pos_stamp
    filename += "_" + ato_deg_stamp

    full_filename = p(filepath / (str(filename) + '.h5'))

    #Q-fit with 3 linwdwidths of data
    Qfit, linewidth, fit_peak_db, fc_fit= df.Q_fit(mag_data**2, vna_freq_points, 1, f0[0],w3db[0], peak_height[0], True, True, filepath,filename+'.pdf')
    if up_down == 'u':
        next_vna_fc = df.roundup(fc_fit - 0.5*linewidth, vna_rbw)
    else:
        next_vna_fc = df.roundup(fc_fit + 0.5*linewidth, vna_rbw)
    next_ato_pos = int(round(abs(mode_map.eval(x = next_vna_fc) - mode_map.eval(x = fc_fit))))
    ato_step = int(next_ato_pos)
    print('fc_fit: ' + str(fc_fit) + ',lw: ' + str(int(linewidth)) + ', Next f_c: ' + str(int(next_vna_fc)) + ', Next ato_step: ' + str(ato_step) + ', Next pheight_db: ' +str(peakheight))
    #turn VNA off
    vnass.power_on_off('OFF')
    time.sleep(1)
#=======================================================================================================================================
    # Send fc - offset to Synthesizer for IF signal to be digitized
    synth.write(":OUTP:STAT ON") #turn on rf state
    synth_fc = fc_fit - digi_fc # set synth below cavity freq
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
        dset.attrs['ato_deg'] = current_position
        dset.attrs['Q3db'] = Q3db
        dset.attrs['Qfit'] = Qfit
        dset.attrs['fit_peak_db'] = fit_peak_db
        dset.attrs['linewidth'] = linewidth
        dset.attrs['temp'] = temperature
        dset.attrs['time'] = t
        dset.attrs['synth_fc'] = synth_fc
        dset.attrs['synth_pow'] = synth_p
        dset.attrs['integration_time'] = wait_time #this will be the previous scan wait time

# #=======================================================================================================================================
#     subprocess.Popen(r"cd C:\Users\equslab\AppData\Local\Programs\Python\Python38-32& python Digitize_labview32.py " + str(full_filename),shell=True)
#     print('Integrating for %.2f mins' %(wait_time/60)) #convert to mins)
#     time.sleep(wait_time)
#     time.sleep(1)

#=======================================================================================================================================
#if using dynamic scan rate
    this_beta = beta_freq_function(fc_fit)
    scan_time_factor = df.beta_scan_time(this_beta)
    print(f'This: {this_beta} and scan_time_factor: {scan_time_factor}')
    wait_time = default_scan_time/scan_time_factor
    digi_n_sweeps = int(wait_time//(17.179869184))
    subprocess.Popen(r"cd C:\Users\equslab\AppData\Local\Programs\Python\Python38-32& python Digitize_labview32_scan_rate.py " + str(full_filename) + ' ' + str(digi_n_sweeps),shell=True)
    print('Digitizing for %.2f mins' %(wait_time/60)) #convert to mins)
    wait_time = digi_n_sweeps*(17.179869184)
    time.sleep(wait_time)
    time.sleep(1)

#=======================================================================================================================================
    #Noise cal
    cal_synth_fc = synth_fc + noise_cal_offset  # set synth below cavity freq
    synth.write(":SOUR:FREQ:CW " + str(int(cal_synth_fc)))  # set frequnecy to cal_synth_fc
    noise_cal_filename = p(filepath / ('noise_cal_'+ sweep_type + "_" + fcent_stamp + '_synth_fc_' + str(int(cal_synth_fc)) + '.h5'))
    subprocess.Popen(r"cd C:\Users\equslab\AppData\Local\Programs\Python\Python38-32& python Digitize_labview32_noise_cal.py " + str(noise_cal_filename),shell=True)
    print('Digitizing for %0.2f mins' %(cal_wait_time/60)) #convert to mins)
    time.sleep(cal_wait_time)
    time.sleep(1)
    synth.write(":OUTP:STAT OFF")  # turn off rf state so VNA trace can be taken.
#retun to top

if measure_temp:
    lakesm.disconnect() # Disconnect from Lakeshore if actively measured temperature
synth.close()
anc.close()
#=======================================================================================================================================

