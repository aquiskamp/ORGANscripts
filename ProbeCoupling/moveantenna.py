"""Finds desired coupling constant through LINEAR antenna movements"""

__author__ = 'Deepali Rajawat'

import time

import matplotlib.pyplot as plt
import numpy as np
import pyvisa
from tqdm import tqdm
import gather_data as gd
from attocube.attocube_usb import ANC300
from pathlib import Path as p
import Antenna_motor.coupling_functions as cf
import matplotlib.animation as ani

# ------------------------------------SETUP-------------------------------------------

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']
anc = ANC300()
methodNo = 1

# Folder To Save Files to:
exp_name = 'moveantennatest'
filepath = p.home() / 'OneDrive' / 'Documents' / '2022' / 'SEM 1' / 'Research' / 'data' / exp_name

setVoltage = {'x': 45}  # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'x': 1000}  # freq in, time for each step = 0.001
step_size = 50  # if step size 50, should move 0.25 mm with each step size
step_size_small = 10 # 0.05 mm
step_linear = 25 #for method 2
big_window = 0.2
small_window = 0.01

anc.freq(setFreq)
anc.V(setVoltage)
anc.ground()

# capacitance is an indicator of heat from piezo
# each step is 3.5 um for this model OR 5 um at room temperature, NEED TO CHECK MODEL

# ------------------------- enter sweeping parameters and do preliminary sweep --------------------------------
params = gd.input_popup(True)  # enter sweep parameters
ready_data, db_data, z_data, freq_data, f0, fspan = gd.gather_data(params, True)  # gather data at desired span
fig1 = gd.present_data(freq_data, z_data)  # present data
desiredbeta = params[6]

# ------------------------- get values and add to arrays for plotting -----------------------------------------
current_beta = gd.getbetafromphase(freq_data, z_data)  # get current beta
# dips, f0, dips_dict = cf.dipfinder(db_data, freq_data, p_width=2, prom=2, Height=18)  # get resonant frequency
fitresults = gd.fit_data(freq_data, z_data, db_data, params[0], params[1])  # to get Q, not sure if necessary
Ql = fitresults['Ql']

coupling_array = [current_beta]  # lists perform better for appending over numpy arrays
Ql_array = [Ql]
antenna_depth = [0.]
resfreq_array = [f0]
cap = []  # idk

upperbeta = desiredbeta + big_window
lowerbeta = desiredbeta - big_window
smallupperbound = desiredbeta + small_window
smalllowerbound = desiredbeta - small_window
n = 0
# -------------------------------- move antenna close to beta value -----------------------------------
match methodNo:
    case 1:
        # method 1: linear movements, but either big steps or small steps depending on how close it is to the value.
        while current_beta > upperbeta or current_beta < lowerbeta:
            if current_beta <= lowerbeta:
                anc.step('x', step_size, 'd')
            else:
                anc.step('x', step_size, 'u')

            # gather new data
            ready_data, db_data, z_data, freq_data, f0, fspan = gd.gather_data(params, True)
            current_beta = gd.getbetafromphase(freq_data, z_data)
            fitresults = gd.fit_data(freq_data, z_data, db_data, f0,
                                     fspan)  # to get Q, not sure if necessary
            Ql = fitresults['Ql']

            # add data
            coupling_array.append(current_beta)
            Ql_array.append(Ql)
            antenna_depth.append(float(antenna_depth[-1]) + 0.25)
            resfreq_array.append(f0)
            cap.append(anc.cap())

            # update figure
            gd.update_graph(fig1, db_data, freq_data)

        # start doing smaller steps when close
        while not (smalllowerbound <= current_beta <= smallupperbound):  # random no for now
            n += 1
            if current_beta <= smalllowerbound:
                anc.step('x', step_size_small, 'd')
            elif current_beta >= smallupperbound:
                anc.step('x', step_size_small, 'u')

                # gather new data
                ready_data, db_data, z_data, freq_data, f0, fspan = gd.gather_data(params, True)
                current_beta = gd.getbetafromphase(freq_data, z_data)
                fitresults = gd.fit_data(freq_data, z_data, db_data, f0,
                                         fspan)  # to get Q, not sure if necessary
                Ql = fitresults['Ql']

                # add data
                coupling_array.append(current_beta)
                Ql_array.append(Ql)
                antenna_depth.append(float(antenna_depth[-1]) + 0.05)
                resfreq_array.append(f0)
                cap.append(anc.cap())

                # update figure
                gd.update_graph(fig1, db_data, freq_data)

            if n == 50:
                print("Could not converge after 50 iterations!")
                break;

        # plot everything
        # antenna depth vs coupling, resonant freq, and q facto
        fig2, axs = plt.subplots(2, 2)
        axs[0, 0].plot(antenna_depth, coupling_array)
        axs[0, 1].plot(antenna_depth, Ql_array)
        axs[1, 0].plot(antenna_depth, resfreq_array)
        axs[1, 1].plot(antenna_depth, cap)

    case 2:
        # regular linear movements, assuming the antenna is all the way out.
        # shows range of antenna depth vs coupling and res freq, as well as effect of heat
        for a in range(50):
            anc.step('x',step_linear, 'd')

            # gather data
            ready_data, db_data, z_data, freq_data, f0, fspan = gd.gather_data(params, True)
            current_beta = gd.getbetafromphase(freq_data, z_data)
            fitresults = gd.fit_data(freq_data, z_data, db_data, f0,
                                     fspan)  # to get Q, not sure if necessary
            Ql = fitresults['Ql']

            # add data
            coupling_array.append(current_beta)
            Ql_array.append(Ql)
            antenna_depth.append(float(antenna_depth[-1]) + 0.05)
            resfreq_array.append(f0)
            cap.append(anc.cap())

            #

# could do steps or continuous run?
