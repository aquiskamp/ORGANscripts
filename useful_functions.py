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
    Qs = [f0s / (vna_rbw * widths)]
    peak_heights = peaks[1]['peak_heights']

    return peaks[0], f0s, Qs, peak_heights
