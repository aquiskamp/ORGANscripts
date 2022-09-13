import numpy as np
from scipy.signal import find_peaks
from scipy.signal import peak_widths
from scipy.signal import peak_prominences
import matplotlib.pyplot as plt

def find_nearest(a, a0):
    "Element in nd array `a` closest to the scalar value `a0`"
    idx = np.abs(a - a0).argmin()
    return a.flat[idx]

def find_nearest_pos(a, a0):
    "position in nd array `a` closest to the scalar value `a0`"
    idx = np.abs(a - a0).argmin()
    return idx

def full_freq_Q3db(data_db, freq_list, prom, peak_width, rel, window, Height, xmin, xmax):
    '''find the peaks based on some parameters and then slide between tuning steps'''
    # Find peaks
    vna_rbw = freq_list[1] - freq_list[0] #in Hz
    minpos = find_nearest_pos(freq_list, xmin)
    maxpos = find_nearest_pos(freq_list, xmax)
    data = data_db[minpos:maxpos]
    freq_croppped = freq_list[minpos:maxpos]
    peaks = find_peaks(data, width=peak_width, prominence=prom, rel_height=rel, wlen=window, height=Height)
    prominences, left_bases, right_bases = peak_prominences(data, peaks[0])

    # Create constant offset as a replacement for prominences
    offset = np.full_like(prominences, 3)

    # Calculate widths at x[peaks] - offset * rel_height
    widths, h_eval, left_ips, right_ips = peak_widths(data, peaks[0], rel_height=1,prominence_data=(offset, left_bases, right_bases))

    f0s = freq_croppped[peaks[0]]
    Qs = f0s / (vna_rbw * widths)
    peak_heights = peaks[1]['peak_heights']

    return peaks[0], f0s, Qs, peak_heights


def move_figure(position="top-left"):
    '''
    Move and resize a window to a set of standard positions on the screen.
    Possible positions are:
    top, bottom, left, right, top-left, top-right, bottom-left, bottom-right
    '''

    mgr = plt.get_current_fig_manager()
    #gr.full_screen_toggle()  # primitive but works to get screen size
    py = mgr.canvas.height()
    px = mgr.canvas.width()

    d = 20  # width of the window border in pixels
    if position == "top":
        # x-top-left-corner, y-top-left-corner, x-width, y-width (in pixels)
        mgr.window.setGeometry(d, 4*d, px - 2*d, py/2 - 4*d)
    elif position == "bottom":
        mgr.window.setGeometry(d, py/2 + 5*d, px - 2*d, py/2 - 4*d)
    elif position == "left":
        mgr.window.setGeometry(d, 4*d, px/2 - 2*d, py - 4*d)
    elif position == "right":
        mgr.window.setGeometry(px/2 + d, 4*d, px/2 - 2*d, py - 4*d)
    elif position == "top-left":
        mgr.window.setGeometry(d, 4*d,600,500)
    elif position == "top-right":
        mgr.window.setGeometry(px/2 + d, 4*d, px/2 - 2*d, py/2 - 4*d)
    elif position == "bottom-left":
        mgr.window.setGeometry(d, py/2 + 5*d, px/2 - 2*d, py/2 - 4*d)
    elif position == "bottom-right":
        mgr.window.setGeometry(px/2 + d, py/2 + 5*d, px/2 - 2*d, py/2 - 4*d)
    elif position == "desktop":
        mgr.window.setGeometry(20*d, 6*d,700,600)
    elif position == "desktop2":
        mgr.window.setGeometry(60 * d, 6 * d, 700, 600)