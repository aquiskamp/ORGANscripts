
import gather_data as gd
import cryolib.general as gen
import numpy as np
import Antenna_motor.coupling_functions as cf
from pathlib import Path as p

# ---reading VNA and presenting tings ----------
#params = gd.input_popup(False)
#ready_data, db_data, freq_data = gd.gather_data(params, True)
#gd.present_data(db_data, freq_data, params[0], params[1])


#-----reading file and fitting tings----------
path = r"C:\Users\deepa\PycharmProjects\pythonProject\Deepali_single_sweep.hdf5"

freq, vna, param  = gd.read_h5_file(path)  #vna_dataset is the original form

db_data = gen.complex_to_dB(vna)

z_data_raw = np.transpose(vna)
z = z_data_raw[:, 0] + z_data_raw[:, 1] * 1j

gd.fit_data(freq,z, db_data, param[0], param[1])




#gd.present_data(db_data, freq, param[0], param[1])




