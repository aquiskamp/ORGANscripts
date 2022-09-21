__author__ = 'Deepali Rajawat'

# dont forget to import things
import time

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
from scipy.signal import find_peaks
from scipy import stats, signal


# variables

# Generates popup box for user inputs
# Input Prompts: "Centre Frequency (Hz)", "Frequency Span (Hz)", "Bandwidth (Hz)",
# "No. Points", "No. Averages", "Power (dBm)"
# Param boolean default inserts default parameters instead of user input.
def input_popup(default):
    text = "Enter the following details:"
    title = "VNA Sweep Parameters"
    input_list = ["Centre Frequency (Hz)", "Frequency Span (Hz)", "Bandwidth (Hz)", "No. Points", "No. Averages",
                  "Power (dBm)", "Coupling Constant (β)"]
    if default is True:
        param = np.array([6280000000, 100000000, None, 1601, 1, None, 2])
    else:
        output = multenterbox(text, title, input_list)
        param = np.array(output)
    # message = "Entered details are in form of list :" + str(output)
    # msg = msgbox(message, title)

    dat_dtype = {
        'names': ('Fcent (Hz)', 'Fspan (Hz)', 'BW (Hz)', 'NPoints', 'NAverages', 'Power (dBm)', 'Coupling Constant'),
        'formats': ('f8', 'f8', 'f8', 'i', 'i', 'f8', 'f8')}
    dat = np.zeros(7, dat_dtype)
    table_data = PrettyTable(dat.dtype.names)
    table_data.add_row(param)

    print("Loaded Settings:")
    print(table_data)

    return param


def connect():
    channel = "1"  # VNA Channel number
    vnass.set_module(channel)  # do i need channel?
    vnass.establish_connection()  # establish connection to vna


def write_summary(fcent, antenna_depth, coupling_array, resfreq_array, contrast_arr, desired_beta=2, steps=[]):
    t = datetime.now(timezone('Australia/Perth')).strftime("%Y_%m_%d %H_%M_%S")
    time_stamp = "time=%s" % t
    filepath = p.home()
    filename = "res_coupling_depth" + str(fcent) + "_" + time_stamp
    full_filename = p(filepath / (str(filename) + '.h5'))
    print(full_filename)

    with h5py.File(full_filename, 'w') as f:
        aset = f.create_dataset('Antenna Depth', data=antenna_depth, compression='gzip', compression_opts=6)  # VNA dset
        fdset = f.create_dataset(' Res Freq', data=resfreq_array, compression='gzip', compression_opts=6)
        cset = f.create_dataset('Coupling Constant', data=coupling_array, compression='gzip', compression_opts=6)
        dset = f.create_dataset('Dip Contrast', data=contrast_arr, compression='gzip', compression_opts=6)
        sset = f.create_dataset('Steps', data=steps, compression='gzip', compression_opts=6)
        fdset.attrs['f_final'] = fcent
        cset.attrs['desired_beta'] = desired_beta


def read_summary(filename):
    with h5py.File(filename, 'r') as f:  # file will be closed when we exit from WITH scope
        f.visititems(print_h5_struct)  # print all strustures names
        antennadepth = f['Antenna Depth'][()]
        resfreq = f[' Res Freq'][()]  # remember this is still complex
        couplingconstants = f['Coupling Constant'][()]
        contrast = f['Dip Contrast'][()]
        steparr = f['Steps'][()]

    # TODO add attributes as well

    return antennadepth, resfreq, couplingconstants, contrast, steparr


def finddips(data, freq, p_width, prom, Height):
    # Find peaks with data given as db
    dips = find_peaks(-data, prominence=prom, height=Height, width=p_width)
    f0 = 0
    if (len(dips[0]) > 0):
        f0 = freq[dips[0][(dips[1]["peak_heights"]).argmax()]]
    if f0 == 0:
        f0 = freq[np.argmin(data)]

    return dips[0], f0, dips


# returns depth of dip, could also use finddips --> explore later

def contrast(db_data):
    return np.max(db_data) - np.min(db_data)


# Gathers data from VNA and writes to hdf5 file if specified
# returns sweep data and transpose of sweep data.

def gather_data(params, writefile):
    # check if connected NEED TO DO, NEED TO RETURN INSTANCE SO I CAN QUERY

    # do initial sweep
    sweep_data = vnass.sweep(params)  # Do a sweep with these parameters
    db_data = gen.complex_to_dB(sweep_data)
    ready_data = np.transpose(sweep_data)
    z_data = ready_data[:, 0] + ready_data[:, 1] * 1j

    fcent, fspan, bandwidth, npoints, average, power, desiredbeta = params
    freq_data = gen.get_frequency_space(fcent, fspan, npoints)

    # find actual resonant frequency and how far off initial sweep was
    dips, f0, dips_dict = finddips(db_data, freq_data, p_width=2, prom=2, Height=3)  # get frequency of dip
    dip_difference = (abs(f0 - fcent) / fspan) * 100
    print("i am in gather data, dip difference is ", dip_difference)

    # if the difference is larger than 1%, resweep and reduce span to increase resolution
    # i dont think this needs to be within an if statement each time
    # if dip_difference > 1:
    newfreq, newdb, desiredhalfspan = find_desired_span(db_data, freq_data, f0)
    params[0] = f0
    params[1] = int(desiredhalfspan * 2)
    fspan = params[1]
    freq_data = gen.get_frequency_space(f0, fspan, npoints)

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
            # fdset.attrs['vna_pow'] = power
            fdset.attrs['vna_span'] = fspan
            fdset.attrs['vna_pts'] = npoints
            fdset.attrs['vna_ave'] = average
            fdset.attrs['vna_rbw'] = fspan / (npoints - 1)
            # fdset.attrs['vna_ifb'] = bandwidth
            # fdset.attrs['nmodes'] = mode_list.shape[0]
            fdset.attrs['time'] = t

        print('SWEEP FINISHED')

    return ready_data, db_data, z_data, freq_data, f0, fspan  # REMEMBER THAT YOU ADDED FO, fspan


def print_h5_struct(name, obj):
    if isinstance(obj, h5py.Dataset):
        print('Dataset:', name)
    elif isinstance(obj, h5py.Group):
        print('Group:', name)


# reads
def read_h5_file(filename):
    print(filename)
    with h5py.File(filename, 'r') as f:  # file will be closed when we exit from WITH scope
        f.visititems(print_h5_struct)  # print all strustures names
        freq = f['Freq'][()]
        vna = f['VNA'][()]  # remember this is still complex
        vna_transpose = np.transpose(vna)
        freq_dataset = f['Freq']
        # vna_dataset = list(f['VNA'])
        fcent = freq_dataset.attrs['f_final']
        power = 0
        # freq_dataset.attrs['vna_pow']
        fspan = freq_dataset.attrs['vna_span']
        npoints = freq_dataset.attrs['vna_pts']
        average = 0
        # average = freq_dataset.attrs['vna_ave']
        bandwidth = 0
        # freq_dataset.attrs['vna_ifb']
        print(
            "Centre Frequency (Hz) : %d \n Frequency Span (Hz): %d \n Bandwidth (Hz): %d \n No. Points: %d \n No. "
            "Averages : %d \n Power (dBm) : %d "
            % (fcent, fspan,
               bandwidth,
               npoints, average, power))
        params = fcent, fspan, bandwidth, npoints, average, power
    return freq, vna_transpose, params


# this is wrong, must change later
def find_desired_span(db_data, f_data, f0, z_data=None):
    # derive 3dB baseline
    # baseline_vals = pu.baseline(-db_data, deg=2)
    # threedbline = -baseline_vals - 3
    #
    # # find point of intersection
    # idx = np.argwhere(np.diff(np.sign(db_data - threedbline))).flatten()
    # threedbbandwidth = f_data[idx[1]] - f_data[idx[0]]  # assuming baseline doesnt intersect

    # attempt two - simply use the max value as the baseline and take 3db away from that
    dbppoint = np.max(db_data) - 3
    threedbline = np.full_like(db_data, dbppoint)
    idx = np.argwhere(np.diff(np.sign(db_data - threedbline))).flatten()  # idk if this statement works
    if len(idx) != 2 or (
            len(idx) == 2 and 2 * (f_data[idx[1]] - f_data[idx[0]]) < 4e6):  # TODO remove if this does not work

        desiredhalfspan = 100e6 / 4  # should maybe be better
    else:
        threedbbandwidth = f_data[idx[1]] - f_data[idx[0]]
        desiredhalfspan = 2 * threedbbandwidth

    # derive desired span and return new data sets with that span

    print("new span is", 2 * desiredhalfspan)
    maxfreq = f0 + desiredhalfspan
    minfreq = f0 - desiredhalfspan
    max = cf.find_nearest_pos(f_data, maxfreq)
    min = cf.find_nearest_pos(f_data, minfreq)
    newfreq = f_data[min:max]
    newdbdata = db_data[min:max]

    # plot for NOW remove later
    # fig, axs = plt.subplots(2)
    #
    # plt.ylabel('S11 (dB)')
    # plt.xlabel('Frequency (GHz)')
    # plt.title("f = %.3f GHz" % (f0 / 1e9), fontsize=16)
    # axs[0].plot(f_data, db_data, f_data, threedbline)
    # axs[1].plot(newfreq, newdbdata)
    # plt.show()

    if z_data is not None:
        newz = z_data[min:max]
        return newfreq, newdbdata, desiredhalfspan, newz

    return newfreq, newdbdata, desiredhalfspan


# processes data and shows it in a graph. No function fitting or calculation of the coupling constant occurs in this
# function. Also finds how far the dip is from the centre of the graph. (necessary in later stages (func fitting)?)
def present_data(db_data, freq_data, fcent, fspan):
    plt.ion()  # makes graph interactive
    dips, f0, dips_dict = finddips(db_data, freq_data, p_width=2, prom=2, Height=18)  # get frequency of dip
    # dip_difference = (abs(f0 - fcent) / fspan) * 100
    # txt = "Dip frequency (GHz): %.3f\n Centre Frequency (GHz) : %.3f \n Percentage difference : %d%%\n" % (
    #     f0, fcent, dip_difference)
    # print(txt)

    if fspan >= 30e6:
        freq_data, db_data, halfspan = find_desired_span(db_data, freq_data, f0)

    # plot figure with correct span
    fig = plt.figure()
    plt.ylabel('S11 (dB)')
    plt.xlabel('Frequency (GHz)')
    plt.title("f = %.3f GHz" % (fcent / 1e9), fontsize=16)
    line1, = plt.plot(freq_data, db_data)
    # plt.text(10, 10, txt)
    plt.show()  # neccessary?

    return fig, line1


# no idea if this works
def update_graph(fig, line1, newdb, newfreq):
    line1.set_xdata(newfreq)
    line1.set_ydata(newdb)
    fig.canvas.draw()
    fig.canvas.flush_events()
    time.sleep(0.1)


# unwraps phase and guesses delay based off that
def bootleg_delay(f_data, z_data):
    phase = np.unwrap(np.angle(z_data))
    gradient, intercept, r_value, p_value, std_err = stats.linregress(f_data, phase)
    delayguess = gradient * (-1.) / (np.pi * 2.)
    return delayguess


def plotunwrappedphase(f_data, z_data, f0, fspan, iteration=0):
    # plt.ion()
    phase = np.unwrap(np.angle(z_data))
    slope = np.gradient(phase) * 100  # = phase[1:]-phase[0:-1]
    slop3 = np.gradient(phase) / np.gradient(f_data / 1e9)

    # try windowing
    window = 0.2
    minpos = cf.find_nearest_pos(f_data, f0 - fspan / 8)
    maxpos = cf.find_nearest_pos(f_data, f0 + fspan / 8)
    fwindow = f_data[minpos:maxpos]
    win2 = int(len(z_data) / 4)
    fwindow2 = f_data[win2:-win2]
    phase2 = phase[win2:-win2]
    slope2 = slope[win2:-win2]

    b, a = signal.butter(4, 0.2, 'low', analog=False)
    y = signal.filtfilt(b, a, phase2, padlen=150)
    slope3 = np.gradient(y) * 100

    slope3 = slope3 - np.mean(slope3)

    phasewindow = np.unwrap(np.angle(z_data[minpos:maxpos]))
    slopewindow = np.gradient(phasewindow) * 100

    # fig1 = plt.figure(1)
    # plt.ylabel('arg |S11| ')
    # plt.xlabel('Frequency (GHz)')
    # plt.title("Phase", fontsize=16)
    # plt.plot(f_data, phase)

    plt.figure()  # makes sure each one is in a different figure
    plt.ylabel('arg |S11| ')
    plt.xlabel('Frequency (GHz)')
    plt.title("Phase", fontsize=16)
    txt = "Centre Frequency (GHz) : %d \n iteration : %d\n Absolute max: %.5f\n ABSOLUTE MAX: %.5F \n Beta value: %.3f" % (
        f0, iteration, slope2[np.argmax(np.abs(slope2))], slope3[np.argmax(np.abs(slope3))], getbeta2(z_data))
    plt.text(f0, 0, txt, fontsize=12)
    plt.plot(fwindow2, phase2, fwindow2, slope2, fwindow2, y, fwindow2, slope3)
    # plt.plot(f_data, phase, f_data,slope)

    plt.show()


# plt.show()


def getbetafromphase(z_data):
    mag_data = abs(z_data)
    powerbeta1 = cf.power_beta(20 * np.log10(mag_data).min(), 20 * np.log10(mag_data).max())
    powerbeta2 = 1 / powerbeta1

    phase = np.unwrap(np.angle(z_data))
    slope = np.gradient(phase) * 100
    window = int(len(z_data) / 4)  # window by half, should i also times it by something?
    slope_windowed = slope[window:-window]
    maxidx = np.argmax(np.abs(slope_windowed))
    grad = slope_windowed[maxidx]

    # print("max",grad)
    # from fit data it should actually be: z = overcoupled (positive) , s = undercoupled (negative) actually positive

    # TODO has issues sometimes when superovercoupled, need to either give larger default fspan or need to take in
    #  history of beta values to determine the right one

    if grad > 0 or abs(grad) < 0.8:
        # abs grad < 0.8 is when super undercoupled and liable to noise
        if powerbeta1 < 1:
            beta = powerbeta1
        else:
            beta = powerbeta2
        print("Undercoupled! Beta is", beta)
    else:
        if powerbeta1 > 1:
            beta = powerbeta1
        else:
            beta = powerbeta2
        print("Overcoupled! Beta is", beta)
    return beta


def getbeta2(z_data):
    mag_data = abs(z_data)
    powerbeta1 = cf.power_beta(20 * np.log10(mag_data).min(), 20 * np.log10(mag_data).max())
    powerbeta2 = 1 / powerbeta1

    phase = np.unwrap(np.angle(z_data))
    # slope = np.gradient(phase) * 100
    window = int(len(z_data) / 4)  # window by half, should i also times it by something?

    b, a = signal.butter(4, 0.2, 'low', analog=False)
    y = signal.filtfilt(b, a, phase, padlen=150)
    slope3 = np.gradient(y) * 100
    slope3 = slope3 - np.mean(slope3)

    slope_windowed = slope3[window:-window]
    maxidx = np.argmax(np.abs(slope_windowed))
    grad = slope_windowed[maxidx]

    if grad > 0:
        # abs grad < 0.8 is when super undercoupled and liable to noise
        if powerbeta1 < 1:
            beta = powerbeta1
        else:
            beta = powerbeta2
        print("Undercoupled! Beta is", beta)
    else:
        if powerbeta1 > 1:
            beta = powerbeta1
        else:
            beta = powerbeta2
        print("Overcoupled! Beta is", beta)
    return beta


def gettodesiredbeta(current_beta, desiredbeta, anc, antenna_depth, coupling_array, resfreq_array,contrast_arr, stepsarr, params):

    f0 = params[0]
    big_window = 0.2
    small_window = 0.01

    upperbeta = desiredbeta + big_window  # 2.2
    lowerbeta = desiredbeta - big_window  # 1.8
    smallupperbound = desiredbeta + small_window  # 2.01
    smalllowerbound = desiredbeta - small_window  # 1.99
    n = 0
    i = 0

    step_size = 50  # if step size 50, should move 0.25 mm with each step size
    step_size_small = 10

    while current_beta > upperbeta or current_beta < lowerbeta:
        i += 1
        if current_beta <= lowerbeta:
            anc.step('y', step_size, 'd')
            print("stepping down!")
            antenna_depth.append(float(antenna_depth[-1]) + 0.005 * step_size)

        else:
            anc.step('y', step_size, 'u')
            print("stepping up!")
            antenna_depth.append(float(antenna_depth[-1]) - 0.005 * step_size)

        # gather new data
        ready_data, db_data, z_data, freq_data, f0, fspan = gather_data(params, False)

        # update the params hopefully this works
        params[0] = f0
        params[1] = fspan

        current_beta = getbeta2(z_data)         # update current beta
        dipcontrast = contrast(db_data)         # update dip size

        # add data
        coupling_array.append(current_beta)
        resfreq_array.append(f0)
        contrast_arr.append(dipcontrast)
        stepsarr.append(stepsarr[-1] + step_size)

    # start doing smaller steps when close
    # while not within 1.99 and 2.01 but within 1.8 and 2.2
    while not (smalllowerbound <= current_beta <= smallupperbound) and (
            lowerbeta <= current_beta <= upperbeta):
        n += 1
        print("in small loop now, n =", n)
        if current_beta <= smalllowerbound:
            anc.step('y', step_size_small, 'd')
            antenna_depth.append(float(antenna_depth[-1]) + 0.005 * step_size_small)
        elif current_beta >= smallupperbound:
            anc.step('y', step_size_small, 'u')
            antenna_depth.append(float(antenna_depth[-1]) - 0.005 * step_size_small)

        # gather new data
        ready_data, db_data, z_data, freq_data, f0, fspan = gather_data(params, False)
        # update params, hopefully this works, honestly probably dont need to do for this func, only when rotor moving
        # todo if updating params does not work remove
        params[0] = f0
        params[1] = fspan

        # update beta and dip depth
        current_beta = getbeta2(z_data)
        dipcontrast = contrast(db_data)

        # add data
        coupling_array.append(current_beta)
        resfreq_array.append(f0)
        contrast_arr.append(dipcontrast)
        stepsarr.append(stepsarr[-1] + step_size_small)

        if n == 50:
            print("Could not converge after 50 iterations!")
            break

    write_summary(f0, antenna_depth, coupling_array, resfreq_array, contrast_arr, desired_beta=desiredbeta)

    return current_beta, antenna_depth, coupling_array, resfreq_array, contrast_arr


def fit_data(f_data, z_data, db_data, fcent, fspan):
    # find percentage difference and then centre and fit to desired span
    dips, f0, dips_dict = finddips(db_data, f_data, p_width=2, prom=2, Height=15)

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
    # port2.plotall()
    couplingcoeff = port2.fitresults['Qc'] / port2.fitresults['Ql'] - 1
    powerbeta1 = cf.power_beta(20 * np.log10(abs(z_data)).min(), 20 * np.log10(abs(z_data)).max())
    powerbeta2 = 1 / powerbeta1
    getbetafromphase(newz)
    port2.fitresults['beta'] = couplingcoeff
    port2.fitresults['PB'] = np.array([powerbeta1, powerbeta2])
    print("BETA = ", couplingcoeff, "BETA (square version) = ", powerbeta1, powerbeta2)
    print("Fit results:", port2.fitresults)

    return port2.fitresults
