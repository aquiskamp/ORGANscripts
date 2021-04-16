__author__ = 'Nikita Kostylev'
__version__ = '20.03.2015_1.0'

import numpy as np
import math

# Convert an an array of complex values to dB
# complex_values: [[real vals], [complex vals]]
# returns numpy array [1xN] of amplitudes om dB
def complex_to_dB(complex_values):
    amp_data = abs(complex_values[0, :] + 1j * complex_values[1, :])
    log_amp_data = 20 * np.log10(amp_data)
    return log_amp_data


# Calculate an array of frequencies
# fcent: central frequency in Hz
# fspan: Span in Hz
# npoints: number of points per span
# returns array [1xN] of frequency values
def get_frequency_space(fcent, fspan, npoints):
    freq_data = np.linspace(fcent - fspan / 2, fcent + fspan / 2, npoints)
    return freq_data


# Return the frequency of the peak in the current data array
# freq_data: array with frequency values for current data
# amp_data : array with corresponding amplitudes
# central_offset_factor: how far to check off-centre (0.1-1.0)
# returns frequency of peak
def get_peak(freq_data, amp_data, central_offset_factor):
    span = len(freq_data)
    left =  span // 2 - math.floor((span * central_offset_factor))
    right = left + math.floor((span * central_offset_factor))

    index = left

    max_ind = index
    max = amp_data[index]
    for item in amp_data:
        if amp_data[index] > max:
            max = amp_data[index]
            max_ind = index
        index += 1

        if index > right:
            break

    return freq_data[max_ind]

