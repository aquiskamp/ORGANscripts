"""Finds desired coupling constant through LINEAR antenna movements"""

__author__ = 'Deepali Rajawat'

import time

import matplotlib.pyplot as plt
import numpy as np
import gather_data as gd
from attocube.attocube_usb import ANC300
from pathlib import Path as p

# ------------------------------------SETUP-------------------------------------------

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']
anc = ANC300()
methodNo = 2

# Folder To Save Files to:
exp_name = 'moveantennatest'
filepath = p.home() / 'OneDrive' / 'Documents' / '2022' / 'SEM 1' / 'Research' / 'data' / exp_name

setVoltage = {'y': 45,
              'x': 45}  # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'y': 1000, #this one is linear atm
           'x': 1000}  # freq in, time for each step = 0.001

step_size = 50  # if step size 50, should move 0.25 mm with each step size
step_size_small = 10  # 0.05 mm
step_linear = 30  # for method 2 (0.15)
big_window = 0.2
small_window = 0.01

anc.freq(setFreq)
anc.V(setVoltage)
anc.ground()

# capacitance is an indicator of heat from piezo
# each step is 3.5 um for this model OR 5 um at room temperature, NEED TO CHECK MODEL
# -------------------------- connect ----------------------------------------------------
gd.connect()
# ------------------------- enter sweeping parameters and do preliminary sweep --------------------------------
params = gd.input_popup(True)  # enter sweep parameters
ready_data, db_data, z_data, freq_data, f0, fspan = gd.gather_data(params, True)  # gather data at desired span
# fig1, line1 = gd.present_data(db_data, freq_data, f0, fspan)  # present data
desiredbeta = params[6]

# ------------------------- get values and add to arrays for plotting -----------------------------------------
current_beta = gd.getbeta2(z_data)  # get current beta
# dips, f0, dips_dict = gd.finddips(db_data, freq_data, p_width=2, prom=2, Height=3)  # get resonant frequency
# todo pretty sure this is not needed but double check
dipcontrast = gd.contrast(db_data)

coupling_array = [current_beta]  # lists perform better for appending over numpy arrays
antenna_depth = [0.]
resfreq_array = [f0]
contrast_arr = [dipcontrast]
stepsarr = [0]
rotatearr = [0.]

upperbeta = desiredbeta + big_window  # 2.2
lowerbeta = desiredbeta - big_window  # 1.8
smallupperbound = desiredbeta + small_window  # 2.01
smalllowerbound = desiredbeta - small_window  # 1.99
n = 0
i = 0
# -------------------------------- move antenna close to beta value -----------------------------------
match methodNo:
    case 1:
        # method 1: linear movements, but either big steps or small steps depending on how close it is to the value.
        # while larger than 2.2 or less than 1.8
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
            ready_data, db_data, z_data, freq_data, f0, fspan = gd.gather_data(params, True)
            current_beta = gd.getbeta2(z_data)
            dipcontrast = gd.contrast(db_data)

            # fitresults = gd.fit_data(freq_data, z_data, db_data, f0,
            #                          fspan)  # to get Q, not sure if necessary
            # Ql = fitresults['Ql']

            # add data
            coupling_array.append(current_beta)
            # Ql_array.append(Ql)
            # antenna_depth.append(float(antenna_depth[-1]) + 0.005*step_size)
            resfreq_array.append(f0)
            contrast_arr.append(dipcontrast)
            stepsarr.append(stepsarr[-1] + step_size)

        # start doing smaller steps when close
        # while not within 1.99 and 2.01 but within 1.8 and 2.2
        while not (smalllowerbound <= current_beta <= smallupperbound) and (
                lowerbeta <= current_beta <= upperbeta):  # random no for now
            n += 1
            print("in small loop now, n =", n)
            if current_beta <= smalllowerbound:
                anc.step('y', step_size_small, 'd')
                antenna_depth.append(float(antenna_depth[-1]) + 0.005 * step_size_small)
            elif current_beta >= smallupperbound:
                anc.step('y', step_size_small, 'u')
                antenna_depth.append(float(antenna_depth[-1]) - 0.005 * step_size_small)

            # gather new data
            ready_data, db_data, z_data, freq_data, f0, fspan = gd.gather_data(params, True)
            current_beta = gd.getbeta2(z_data)
            dipcontrast = gd.contrast(db_data)
            # fitresults = gd.fit_data(freq_data, z_data, db_data, f0,
            #                          fspan)  # to get Q, not sure if necessary
            # Ql = fitresults['Ql']

            # add data
            coupling_array.append(current_beta)
            # Ql_array.append(Ql)
            resfreq_array.append(f0)
            contrast_arr.append(dipcontrast)
            stepsarr.append(stepsarr[-1] + step_size_small)

            if n == 50:
                print("Could not converge after 50 iterations!")
                break;

        plt.figure(1)
        plt.title("Coupling Constant", fontsize=16)
        plt.ylabel('Coupling Constant β')
        plt.xlabel('Antenna Depth (mm)')
        plt.plot(antenna_depth, coupling_array)

        plt.figure(2)
        plt.title("Resonant Frequency", fontsize=16)
        plt.ylabel('Resonant Frequency (Hz)')
        plt.xlabel('Antenna Depth (mm)')
        plt.plot(antenna_depth, resfreq_array, 'g-')

        plt.figure(3)
        plt.title("Contrast", fontsize=16)
        plt.ylabel('Constrast (dB)')
        plt.xlabel('Antenna Depth (mm)')
        plt.plot(antenna_depth, contrast_arr, 'r-')
        # write data from plots
        gd.write_summary(f0, antenna_depth, coupling_array, resfreq_array, contrast_arr, desired_beta=desiredbeta)

    case 2:
        # regular linear movements, assuming the antenna is all the way out.
        # shows range of antenna depth vs coupling and res freq, as well as effect of heat
        for a in range(200):  # try 50 for now
            anc.step('y', step_linear, 'd')

            # gather data
            ready_data, db_data, z_data, freq_data, f0, fspan = gd.gather_data(params, True)
            current_beta = gd.getbeta2(z_data)
            dipcontrast = gd.contrast(db_data)

            # add data
            coupling_array.append(current_beta)
            antenna_depth.append(float(antenna_depth[-1]) + 0.005 * step_linear)
            resfreq_array.append(f0)
            contrast_arr.append(dipcontrast)
            stepsarr.append(stepsarr[-1] + step_linear)

        # plot everything
        plt.figure(1)
        plt.title("Coupling Constant", fontsize=16)
        plt.ylabel('Coupling Constant β')
        plt.xlabel('Antenna Depth (mm)')
        plt.plot(antenna_depth, coupling_array)

        plt.figure(2)
        plt.title("Resonant Frequency", fontsize=16)
        plt.ylabel('Resonant Frequency (Hz)')
        plt.xlabel('Antenna Depth (mm)')
        plt.plot(antenna_depth, resfreq_array, 'g-')

        plt.figure(3)
        plt.title("Contrast", fontsize=16)
        plt.ylabel('Constrast (dB)')
        plt.xlabel('Antenna Depth (mm)')
        plt.plot(antenna_depth, contrast_arr, 'r-')
        # write data from plots
        gd.write_summary(f0, antenna_depth, coupling_array, resfreq_array, contrast_arr, desired_beta=desiredbeta)

    case 3:
        # move antenna to desired and then rotate and keep on desired
        # maybe want to get to desiredbeta and desiredfrequency
        # also maybe want to do linear rotating sweep/mode map to understand data more
        current_beta, antenna_depth, coupling_array, resfreq_array, contrast_arr = gd.gettodesiredbeta(current_beta,
                                                                                                       desiredbeta,
                                                                                                       anc,
                                                                                                       antenna_depth,
                                                                                                       coupling_array,
                                                                                                       resfreq_array,
                                                                                                       contrast_arr,
                                                                                                       stepsarr,
                                                                                                       params)

        for b in range(200):
            # rotating
            anc.step('x', step_linear, 'd')  # idk how this rotates
            rotatearr.append()

            # gatherdata
            ready_data, db_data, z_data, freq_data, f0, fspan = gd.gather_data(params, True)
            #
            current_beta = gd.getbeta2(z_data)
            dipcontrast = gd.contrast(db_data)

            # append data
            coupling_array.append(current_beta)
            antenna_depth.append(float(antenna_depth[-1]) + 0.005 * step_linear)
            resfreq_array.append(f0)
            contrast_arr.append(dipcontrast)
            stepsarr.append(stepsarr[-1] + step_linear)
            # move to desiredbeta

            gettodesiredbeta
            # gather
            # append

            # get beta again
