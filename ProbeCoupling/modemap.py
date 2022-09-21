import warnings
import time
import numpy as np
import cryolib.general as gen
import matplotlib.pyplot as plt
from attocube.attocube_usb import ANC300
import gather_data as gd
import vna_single_sweep as vnass
from pathlib import Path as p
import h5py
from attocube.ato_func import ato_hdf5_parser
from matplotlib import cm
from matplotlib.colors import Normalize
from matplotlib.backends.backend_pdf import PdfPages

# ------------------------------------SETUP-------------------------------------------

fmt = "%Y_%m_%d %H_%M_%S"
tz = ['Australia/Perth']
anc = ANC300()

# Folder To Save Files to:
exp_name = 'modemap3'
filepath = p.home() / 'OneDrive' / 'Documents' / '2022' / 'SEM 1' / 'Research' / 'data'

ato_start = 0
ato_end = 3000
step_size = 30  # if step size 50, should move 0.25 mm with each step size
total_steps = int((ato_end - ato_start) / step_size) + 1
db_min = -5
db_max = -50

freq_start = 7.125e9
freq_end = 7.165e9

setVoltage = {'x': 45}  # key-value pair, x is axis, '60' is voltage Volts
setFreq = {'x': 1000}  # freq in, time for each step = 0.001

anc.freq(setFreq)
anc.V(setVoltage)
anc.ground()

steparr = np.arange(ato_start, ato_end + step_size, step_size)

# ------------- connect -----------------
gd.connect()

# --------- set sweeping parameters -----
# remember that span cannot change, should do 7.125 - 7.165
freqspan = int(freq_end - freq_start)
param = np.array([freq_start+(freqspan/2),freqspan, None, 1601, 1, None, 2])
fcent, fspan, bandwidth, npoints, average, power, desiredbeta = param
freq_data = gen.get_frequency_space(fcent, fspan, npoints)

plt.ion()
fig1 = plt.figure("MODE MAP")
plt.draw()

for i, step in enumerate(steparr):
    if step == 0:
        anc.ground()
    else:
        anc.step('x', step_size, 'd')

    # gather data
    sweep_data = vnass.sweep(param)  # Do a sweep with these parameters
    db_data = gen.complex_to_dB(sweep_data)
    ready_data = np.transpose(sweep_data)
    z_data = ready_data[:, 0] + ready_data[:, 1] * 1j

    #append data to file
    with h5py.File(filepath / p(exp_name + '.hdf5'), 'a') as f:
        try:
            if f[str(step)]:
                del (f[str(step)])
        except:
            None

        dset = f.create_dataset(str(step), data=ready_data, compression='gzip', compression_opts=6)  # VNA dset
        try:
            f['Freq']
        except:
            fdset = f.create_dataset('Freq', data=freq_data, compression='gzip', compression_opts=6)
            fdset.attrs['f_final'] = fcent
            if power is None:
                fdset.attrs['vna_pow'] = 0
            else:
                fdset.attrs['vna_pow'] = power
            fdset.attrs['vna_span'] = fspan
            fdset.attrs['vna_pts'] = npoints
            fdset.attrs['vna_rbw'] = fspan / (npoints - 1)
            if bandwidth is None:
                fdset.attrs['vna_ifb'] = 0
            else:
                fdset.attrs['vna_ifb'] = bandwidth
            fdset.attrs['ato_voltage'] = setVoltage['x']
            fdset.attrs['ato_freq'] = setFreq['x']
            fdset.attrs['ato_step'] = step_size
            fdset.attrs['total_steps'] = total_steps
        dset.attrs['ato_pos'] = step

    if i % 5 == 0 and i != 0:
        fig1.clf()
        ax1 = fig1.add_subplot(111)
        mag_data_db, freq, ato_positions = ato_hdf5_parser(filepath / p(exp_name + '.hdf5'))
        phi = ato_positions // step_size
        colour = ax1.imshow(mag_data_db, extent=[phi[0], phi[-1], freq[0], freq[-1]],
                            aspect=(0.8 * (phi[-1] - phi[0]) / (freq[-1] - freq[0])),
                            cmap=plt.cm.get_cmap('viridis'), origin='lower', norm=Normalize(vmin=db_min, vmax=db_max))
        ax1.set_xlabel(r'Phi (Steps)')
        ax1.set_ylabel(r'Frequency (GHz)')
        cb = fig1.colorbar(colour, ax=ax1, fraction=0.0325, pad=0.04)
        cb.set_label('$|S_{21}|$ [dB]')
        cm.ScalarMappable()
        plt.title(exp_name)
        plt.draw()
        plt.pause(0.1)

# save modemap
pp = PdfPages(filepath / (exp_name + '_MODE_MAP.pdf'))
fig1.savefig(pp, format='pdf', dpi=600)
pp.close()

print("ALL VALUES RECORDED. SWEEP COMPLETE.")

for i in range()