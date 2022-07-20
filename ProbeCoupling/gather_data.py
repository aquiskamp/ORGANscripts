__author__ = 'Deepali Rajawat'

# dont forget to import things
from easygui import *
from prettytable import PrettyTable
import numpy as np
import vna_single_sweep as vnass
import cryolib.general as gen
from pathlib import Path as p
import h5py
from datetime import datetime
from pytz import timezone
import matplotlib.pyplot as plt
import Antenna_motor.coupling_functions as cf
import resonator_tools.circuit as circuit
import peakutils as pu
from scipy import stats


# variables

# Generates popup box for user inputs
# Input Prompts: "Centre Frequency (Hz)", "Frequency Span (Hz)", "Bandwidth (Hz)",
# "No. Points", "No. Averages", "Power (dBm)"
# Param boolean default inserts default parameters instead of user input.
def input_popup(default):
    text = "Enter the following details:"
    title = "VNA Sweep Parameters"
    input_list = ["Centre Frequency (Hz)", "Frequency Span (Hz)", "Bandwidth (Hz)", "No. Points", "No. Averages",
                  "Power (dBm)"]
    if default is True:
        param = np.array([7130000000, 100000000, 1000, 3201, 1, -10])
    else:
        output = multenterbox(text, title, input_list)
        param = np.array(output)
    # message = "Entered details are in form of list :" + str(output)
    # msg = msgbox(message, title)

    dat_dtype = {
        'names': ('Fcent (Hz)', 'Fspan (Hz)', 'BW (Hz)', 'NPoints', 'NAverages', 'Power (dBm)'),
        'formats': ('f8', 'f8', 'f8', 'i', 'i', 'f8')}
    dat = np.zeros(7, dat_dtype)
    table_data = PrettyTable(dat.dtype.names)
    table_data.add_row(param)

    print("Loaded Settings:")
    print(table_data)

    return param


# Gathers data from VNA and writes to hdf5 file if specified
# returns sweep data and transpose of sweep data.

def gather_data(params, writefile):
    # gather VNA sweep parameters
    channel = "1"  # VNA Channel number
    vnass.set_module(channel)  # do i need channel?
    vnass.establish_connection()  # establish connection to vna

    sweep_data = vnass.sweep(params)  # Do a sweep with these parameters
    db_data = gen.complex_to_dB(sweep_data)
    ready_data = np.transpose(sweep_data)
    z_data = ready_data[:, 0] + ready_data[:, 1] * 1j

    fcent, fspan, bandwidth, npoints, power, average = params
    freq_data = gen.get_frequency_space(fcent, fspan, npoints)

    # find actual resonant frequency and how far off initial sweep was
    dips, f0, dips_dict = cf.dipfinder(db_data, freq_data, p_width=2, prom=2, Height=15)  # get frequency of dip
    dip_difference = (abs(f0 - fcent) / fspan) * 100

    # if the difference is larger than 1%, resweep and reduce span to increase resolution
    if dip_difference > 1:
        newfreq, newdb, desiredhalfspan = find_desired_span(db_data, freq_data, f0)
        params[0] = f0
        params[1] = int(desiredhalfspan * 2)
        # params[1] = int(fspan / 2)  # idk if you need to typecast

        sweep_data = vnass.sweep(params)  # Do a sweep with these parameters
        db_data = gen.complex_to_dB(sweep_data)
        ready_data = np.transpose(sweep_data)
        z_data = ready_data[:, 0] + ready_data[:, 1] * 1j

    if writefile:
        t = datetime.now(timezone('Australia/Perth')).strftime("%Y_%m_%d %H_%M_%S")
        time_stamp = "time=%s" % t
        filepath = p.home()
        filename = "vna_antennacoupling" + str(fcent) + "_" + time_stamp
        full_filename = p(filepath / (str(filename) + '.h5'))
        print(full_filename)

        with h5py.File(full_filename, 'w') as f:
            full_freq = np.linspace(fcent - fspan // 2, fcent + fspan // 2, ready_data.shape[0])  # freq list in Hz
            dset = f.create_dataset('VNA', data=ready_data, compression='gzip', compression_opts=6)  # VNA dset
            fdset = f.create_dataset('Freq', data=full_freq, compression='gzip', compression_opts=6)
            fdset.attrs['f_final'] = fcent
            fdset.attrs['vna_pow'] = power
            fdset.attrs['vna_span'] = fspan
            fdset.attrs['vna_pts'] = npoints
            fdset.attrs['vna_ave'] = average
            fdset.attrs['vna_rbw'] = fspan / (npoints - 1)
            fdset.attrs['vna_ifb'] = bandwidth
            # fdset.attrs['nmodes'] = mode_list.shape[0]
            fdset.attrs['time'] = t

        print('SWEEP FINISHED')

    return ready_data, db_data, z_data, freq_data


def print_h5_struct(name, obj):
    if isinstance(obj, h5py.Dataset):
        print('Dataset:', name)
    elif isinstance(obj, h5py.Group):
        print('Group:', name)


# reads
def read_h5_file(filename):
    with h5py.File(filename, 'r') as f:  # file will be closed when we exit from WITH scope
        f.visititems(print_h5_struct)  # print all strustures names
        freq = f['Freq'][()]
        vna = f['VNA'][()]  # remember this is still complex
        vna_transpose = np.transpose(vna)
        freq_dataset = f['Freq']
        # vna_dataset = list(f['VNA'])
        fcent = freq_dataset.attrs['f_final']
        power = freq_dataset.attrs['vna_pow']
        fspan = freq_dataset.attrs['vna_span']
        npoints = freq_dataset.attrs['vna_pts']
        average = freq_dataset.attrs['vna_ave']
        bandwidth = freq_dataset.attrs['vna_ifb']
        print(
            "Centre Frequency (Hz) : %d \n Frequency Span (Hz): %d \n Bandwidth (Hz): %d \n No. Points: %d \n No. "
            "Averages : %d \n Power (dBm) : %d "
            % (fcent, fspan, bandwidth, npoints, average, power))
        params = fcent, fspan, bandwidth, npoints, average, power
    return freq, vna_transpose, params


def find_desired_span(db_data, f_data, f0, z_data=None):
    # derive 3dB baseline
    baseline_vals = pu.baseline(-db_data)
    threedbline = -baseline_vals - 3

    # find point of intersection
    idx = np.argwhere(np.diff(np.sign(db_data - threedbline))).flatten()
    threedbbandwidth = f_data[idx[1]] - f_data[idx[0]]  # assuming baseline doesnt intersect

    # derive desired span and return new data sets with that span
    desiredhalfspan = 2 * threedbbandwidth
    print("new span is", 2 * desiredhalfspan)
    maxfreq = f0 + desiredhalfspan
    minfreq = f0 - desiredhalfspan
    max = cf.find_nearest_pos(f_data, maxfreq)
    min = cf.find_nearest_pos(f_data, minfreq)
    newfreq = f_data[min:max]
    newdbdata = db_data[min:max]
    if z_data is not None:
        newz = z_data[min:max]
        return newfreq, newdbdata, desiredhalfspan, newz

    return newfreq, newdbdata, desiredhalfspan


# processes data and shows it in a graph. No function fitting or calculation of the coupling constant occurs in this
# function. Also finds how far the dip is from the centre of the graph. (necessary in later stages (func fitting)?)
def present_data(db_data, freq_data, fcent, fspan):
    plt.ion()  # makes graph interactive
    dips, f0, dips_dict = cf.dipfinder(db_data, freq_data, p_width=2, prom=2, Height=18)  # get frequency of dip
    dip_difference = (abs(f0 - fcent) / fspan) * 100
    txt = "Dip frequency (GHz): %.3f\n Centre Frequency (GHz) : %.3f \n Percentage difference : %d%%\n" % (
        f0, fcent, dip_difference)
    print(txt)

    if fspan >= 30e6:
        freq_data, db_data, halfspan = find_desired_span(db_data, freq_data, f0)

    # plot figure with correct span
    plt.figure()
    plt.ylabel('S11 (dB)')
    plt.xlabel('Frequency (GHz)')
    plt.title("f = %.3f GHz" % (fcent / 1e9), fontsize=16)
    plt.plot(freq_data, db_data)
    plt.text(10, 10, txt)
    plt.show()


# unwraps phase and guesses delay based off that
def bootleg_delay(f_data, z_data):
    phase = np.unwrap(np.angle(z_data))
    gradient, intercept, r_value, p_value, std_err = stats.linregress(f_data, phase)
    delayguess = gradient * (-1.) / (np.pi * 2.)
    return delayguess


def plotunwrappedphase(f_data, z_data):
    plt.ion()
    phase = np.unwrap(np.angle(z_data))
    slope = np.gradient(phase)
    plt.figure()
    plt.ylabel('arg |S11| ')
    plt.xlabel('Frequency (GHz)')
    plt.title("Phase", fontsize=16)
    plt.plot(f_data, phase, f_data, slope)
    plt.show()


def getbetafromphase(f_data, z_data):
    mag_data = abs(z_data)
    powerbeta1 = cf.power_beta(20 * np.log10(mag_data).min(), 20 * np.log10(mag_data).max())
    powerbeta2 = 1 / powerbeta1

    phase = np.unwrap(np.angle(z_data))
    slope = np.gradient(phase)
    maxidx = np.argmax(np.abs(slope))
    grad = slope[maxidx]
    if grad > 0:
        if powerbeta1 > 1:
            beta = powerbeta1
        else:
            beta = powerbeta2
        print("Overcoupled! Beta is", beta)
    else:
        if powerbeta1 < 1:
            beta = powerbeta1
        else:
            beta = powerbeta2
        print("Undercoupled! Beta is", beta)
    return beta


def fit_data(f_data, z_data, db_data, fcent, fspan):
    # find percentage difference and then centre and fit to desired span
    dips, f0, dips_dict = cf.dipfinder(db_data, f_data, p_width=2, prom=2, Height=15)

    dip_difference = ((f0 - fcent) / fspan) * 100
    print("dip difference =", dip_difference)

    # find desired span
    newfreq, newdb, newhalfspan, newz = find_desired_span(db_data, f_data, f0, z_data=z_data)

    # fitdata
    port2 = circuit.reflection_port(newfreq, newz)
    port2.autofit()
    delayguess = bootleg_delay(newfreq, newz)

    mindelay = port2._delay
    minchi = port2.fitresults["chi_square"]
    print("current delay = ", mindelay, "curr chi = ", minchi)
    delays = np.linspace(-2 * delayguess, 2 * delayguess, 100)

    print("GUESS DELAY = ", delayguess)
    for i in delays:
        port2.autofit(electric_delay=i)
        if port2.fitresults["chi_square"] is None:
            continue
        else:
            chi = port2.fitresults["chi_square"]
            fr_err = port2.fitresults["fr_err"]
        if chi < minchi and fr_err < 1e09:
            minchi = chi
            mindelay = i

    print("MIN  CHI, DELAY=", minchi, mindelay)
    port2.autofit(electric_delay=mindelay)
    # port1.plotrawdata()
    port2.plotall()
    couplingcoeff = port2.fitresults['Qc'] / port2.fitresults['Ql'] - 1
    powerbeta1 = cf.power_beta(20 * np.log10(abs(z_data)).min(), 20 * np.log10(abs(z_data)).max())
    powerbeta2 = 1 / powerbeta1
    getbetafromphase(newfreq, newz)
    port2.fitresults['beta'] = couplingcoeff
    port2.fitresults['PB'] = np.array([powerbeta1, powerbeta2])
    print("BETA = ", couplingcoeff, "BETA (square version) = ", powerbeta1, powerbeta2)
    print("Fit results:", port2.fitresults)

    return port2.fitresults
