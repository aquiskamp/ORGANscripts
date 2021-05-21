from functools import lru_cache
import h5py
import numpy as np

def ato_hdf5_parser(fname):
    f = h5py.File(fname,'r')
    freq = f['Freq'][:]/1e9 #in GHz
    ato_positions = sorted(f.keys(), key=lambda item: (int(item.partition(' ')[0])
                               if item[0].isdigit() else float('inf'), item))[:-1]
    phi = np.asarray([int(i) for i in ato_positions])
    total_data = np.array([f[ref][:] for ref in ato_positions])
    
    mag_data = np.sqrt(total_data[:,:,0]**2 + total_data[:,:,1]**2).T
    mag_data_db = 20*np.log10(mag_data)
  
    return mag_data_db, freq, phi