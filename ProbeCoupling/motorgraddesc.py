from pathlib import Path as p

from attocube.attocube_usb import ANC300
import gather_data as gd
import cryolib.general as gen
import numpy as np

# ------------------------------------SETUP-------------------------------------------

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']
anc = ANC300()

# Folder To Save Files to:
exp_name = 'gradientdesctest'
filepath = p.home() / 'Desktop' / 'ORGAN_15GHz' / 'ProbeCoubling' / exp_name

setVoltage = {'x': 60}  # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'x': 1000}  # freq in
anc.freq(setFreq)
anc.V(setVoltage)
anc.ground()


#do preliminary sweep
params = gd.input_popup(False)
ready_data, db_data, freq_data = gd.gather_data(params, True)
gd.present_data(db_data, freq_data, params[0], params[1])

# ato_start = 0
# ato_end = 2200
# ato_step = 20
# total_steps = int((ato_end - ato_start) / ato_step) + 1
# up_down = 'd'  # set to up, to set to down replace 'u' with 'd'
