__author__ = 'Aaron Quiskamp'

import pyvisa
from scipy.signal import find_peaks
from scipy.signal import peak_widths
from scipy.signal import peak_prominences
import numpy as np
from lmfit.models import BreitWignerModel, QuadraticModel, PolynomialModel
import matplotlib.pyplot as plt
import math
from matplotlib.ticker import ScalarFormatter
from pathlib import Path as p
from matplotlib.backends.backend_pdf import PdfPages
x_formatter = ScalarFormatter(useOffset=False)

plt.ion()
fig = plt.figure("VNA DOWNLOAD")
plt.draw()
def beta_scan_time(beta):
    #factor of 8 normalizes function to beta=1 adjust scan time from beta=1
    return 8*beta**2/(1+beta)**3

def connect(gpib):
    # rm.list_resources()   # print available gpib resource names
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(gpib)  # Connect to resource
    resp = inst.query("*IDN?").rstrip("\n") # Check device ID
    print("Connected to Device ID = " + resp)
    return inst

def connect_usb(usb):
    # rm.list_resources()   # print available gpib resource names
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(usb)  # Connect to resource
    print("Connected to Device ID = " + usb)
    return inst

def peakfinder(data, freq, prom, Height):
    bandwidth = freq[1]-freq[0]
    peaks = find_peaks(data, prominence=prom, height=Height)
    prominences, left_bases, right_bases = peak_prominences(data, peaks[0])
    # Create constant offset as a replacement for prominences
    offset = np.full_like(prominences, 3)
    # Calculate widths at x[peaks] - offset * rel_heigh
    widths, h_eval, left_ips, right_ips = peak_widths(
        data, peaks[0], rel_height=1, prominence_data=(offset, left_bases, right_bases))

    f0 = freq[peaks[0]]# central f
    w3db = widths * bandwidth  # 3db width
    Q = f0 / w3db  # Q-estimate
    peak_height = 10 ** np.array(peaks[1]["peak_heights"] / 10)
    pheight_db = peaks[1]["peak_heights"]

    return f0, w3db, Q, peak_height, pheight_db

def find_nearest_pos(a, a0):
    "position in nd array `a` closest to the scalar value `a0`"
    idx = np.abs(a - a0).argmin()
    return idx

def roundup(x,rbw):
    return int(math.ceil(x /rbw )) * int(rbw)


def Q_fit(magdata, freq_list, nlw, f0, w3db, peak_height, plot, save,file_path,file_name):

    minpos = find_nearest_pos(freq_list, f0 - nlw * w3db)
    maxpos = find_nearest_pos(freq_list, f0 + nlw * w3db)

    # input these positions into mag_data
    reduced_data = magdata[minpos:maxpos]
    modef = freq_list[minpos:maxpos]/1e9

    resonator = BreitWignerModel()  # fano-model
    background = QuadraticModel()
    model = resonator + background  # composite model

    # start the fit
    pars = model.left.guess(reduced_data, x=modef) + model.right.guess(reduced_data, x=modef)
    pars['amplitude'].set(value=peak_height, vary=True, expr='')  # set inital val
    pars['sigma'].set(value=w3db/1e9, vary=True, expr='')
    pars['center'].set(value=f0/1e9, vary=True, expr='')
    pars['a'].set(value=-0.001, vary=True, expr='')
    pars['q'].set(value=0, vary=True, expr='')
    fit_pars = model.fit(reduced_data, pars, x=modef)  # fit using guess params
    final_fit = fit_pars.best_fit
    Q = fit_pars.params['center'].value / fit_pars.params['sigma'].value

    if plot == True:
        fig.clf()
        ax = fig.add_subplot(111)
        ax.plot(modef, 10 * np.log10(np.abs(reduced_data)), label=r'Data')
        ax.plot(modef, 10 * np.log10(np.abs(final_fit)),
                label="$Q_L$=" + str(round(Q)) + '\n' + "$f_0$=" + str(round(fit_pars.values['center'], 5))
                      + ' GHz' + '\n' + '$q$=' + str(round(fit_pars.values['q'], 3)))
        plt.ylabel(r'$|S_{21}|$ [dB]', fontsize=12)
        plt.xlabel('Frequency (GHz)', fontsize=12)
        ax.legend()
        ax.xaxis.set_major_formatter(x_formatter)
        ax.tick_params(axis='both', which='major', labelsize=12)
        plt.axis('tight')
        plt.draw()
        plt.pause(0.1)
    if save:
        (file_path/'Q_pdfs').mkdir(parents=True, exist_ok=True)
        pp = PdfPages(file_path/'Q_pdfs'/file_name)
        plt.savefig(pp, format='pdf', dpi=600)
        pp.close()

    return Q, fit_pars.params['sigma'].value*1e9, 10 * np.log10(final_fit.max()), fit_pars.params['center'].value*1e9  # peak trans in dB

