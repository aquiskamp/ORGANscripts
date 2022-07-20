from pathlib import Path as p

from attocube.attocube_usb import ANC300
import gather_data as gd
import cryolib.general as gen
import numpy as np
import gradientdescent as grad
#import argrelextreme
# ------------------------------------SETUP-------------------------------------------

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']
anc = ANC300()

# Folder To Save Files to:
exp_name = 'gradientdesctest'
filepath = p.home() / 'OneDrive' / 'Documents' / '2022' / 'SEM 1' / 'Research' / 'data' / exp_name
setVoltage = {'x': 45}  # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'x': 1000}  # freq in
anc.freq(setFreq)
anc.V(setVoltage)
anc.ground()
targetbeta = 2
learnrate = 30


#do preliminary sweep---------------------------------------------------
params = gd.input_popup(True)
ready_data, db_data, z_data, freq_data = gd.gather_data(params, True)
currentbeta = gd.getbetafromphase(freq_data, z_data)
# fitresults = gd.fit_data(freq_data, z_data, db_data, params[0], params[1])
# currentbeta = fitresults['beta']
print("beta is ", currentbeta)
print("gradient is", grad.gradient(targetbeta, currentbeta))
grad = abs(grad.gradient(targetbeta, currentbeta))


for i in range(5):
    stepsize = int(grad * learnrate)
    if currentbeta < targetbeta:
        print("gradient is", grad)
        print("Undercoupled! Current beta is ", currentbeta, ". Moving stepsize = ", stepsize)
        anc.step('x', stepsize, 'd')
    elif currentbeta > targetbeta:
        print("gradient is", grad)
        print("Overcoupled! Current beta is ", currentbeta, ". Moving stepsize = ", stepsize)
        anc.step('x', stepsize, 'd')
    ready_data, db_data, z_data, freq_data = gd.gather_data(params, False)
    fitresults = gd.fit_data(freq_data, z_data, db_data, params[0], params[1])
    currentbeta = fitresults['beta']
    grad = abs(grad.gradient(targetbeta, currentbeta))

# ato_start = 0
# ato_end = 2200
# ato_step = 20
# total_steps = int((ato_end - ato_start) / ato_step) + 1
# up_down = 'd'  # set to up, to set to down replace 'u' with 'd'
