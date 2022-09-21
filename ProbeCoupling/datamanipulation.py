import matplotlib.pyplot as plt
import numpy as np
import gather_data as gd
import os
import h5py

os.chdir('C:/Users/deepa/OneDrive/Documents/2022/SEM 1/Research/data/7sept_successfullinearsweep')
filename = 'res_coupling_depth7135062500.0_time=2022_09_07 17_36_52.h5'
#
antennadepth, resfreq, couplingconstants, contrast, steparr = \
    gd.read_summary(filename)

os.chdir('C:/Users/deepa/OneDrive/Documents/2022/SEM 1/Research/data/9sept_biglinearsweep')
newname = 'res_coupling_depth6176720164.449373_time=2022_09_09 16_36_57.h5'
antennadepth2, resfreq2, couplingconstants2, contrast2, steparr2 = \
    gd.read_summary(newname)

#attempt to fix coupling constant data specific to linearsweep on 5sept
# couplingconstants[-5:] = 1/couplingconstants[-5:]
# couplingconstants[55] = 1/couplingconstants[55]
# couplingconstants[53] = 1/couplingconstants[53]
# couplingconstants[51] = 1/couplingconstants[51]

newfreq = contrast/max(contrast)
newfreq2 = contrast2/max(contrast2)
plt.figure(1)
plt.title("Resonant Frequency", fontsize=16)
plt.ylabel('Resonant Frequency (Hz)')
plt.xlabel('Antenna Depth (mm)')
plt.plot(antennadepth/max(antennadepth), newfreq,antennadepth2/max(antennadepth2),newfreq2)
#coupling vs depth/steps

fig, ax1 = plt.subplots()
ax1.set_title('Coupling constant relative to antenna depth')
color = 'tab:red'
ax1.set_xlabel('Antenna Depth (mm)')
ax1.set_ylabel('Coupling Constant', color=color)
ax1.plot(antennadepth, couplingconstants, color=color)
ax1.tick_params(axis='x', labelcolor=color)
#
# ax2 = ax1.twiny()  # instantiate a second axes that shares the same y-axis
#
# color = 'tab:blue'
# ax2.set_xlabel('Steps', color=color)  # we already handled the x-label with ax1
# ax2.plot(steparr, couplingconstants, color=color)
# ax2.tick_params(axis='x', labelcolor=color)

fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.show()

#resonant frequency relative to antennadepth
plt.figure(2)
plt.title("Resonant Frequency", fontsize=16)
plt.ylabel('Resonant Frequency (Hz)')
plt.xlabel('Antenna Depth (mm)')
plt.plot(antennadepth, resfreq, 'g-')

#contrast vs antennadepth
plt.figure(3)
plt.title("Contrast", fontsize=16)
plt.ylabel('Constrast (dB)')
plt.xlabel('Antenna Depth (mm)')
plt.plot(antennadepth, contrast, 'r-')

#resonant freq vs coupling
plt.figure(4)
plt.title("Resonant Frequency relative to coupling constant", fontsize=16)
plt.xlabel('Resonant Frequency (Hz)')
plt.ylabel('Coupling Constant')
plt.plot(resfreq, couplingconstants, 'g-')

#coupling vs contrast
plt.figure(5)
plt.title("Dip Contrast relative to coupling constant", fontsize=16)
plt.xlabel('Coupling Constant')
plt.ylabel('Dip Contrast (dB)')
plt.plot(contrast2, couplingconstants2, 'r-')

plt.figure(6)
plt.title("Dip Contrast relative to coupling constant", fontsize=16)
plt.ylabel('Coupling Constant')
plt.xlabel('Dip Contrast (dB)')
plt.plot(contrast2, couplingconstants2, 'r-')





