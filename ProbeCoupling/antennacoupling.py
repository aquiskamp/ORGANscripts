
import gather_data as gd
import cryolib.general as gen


#params = gd.input_popup()
#ready_data, db_data, freq_data = gd.gather_data(params, True)
#gd.present_data(db_data, freq_data, params[0], params[1])



path = r"C:\Users\deepa\PycharmProjects\pythonProject\Deepali_single_sweep_010.hdf5"
freq, vna, param = gd.read_h5_file(path)
db_data = gen.complex_to_dB(vna)

gd.fit_data(freq,vna)


#gd.present_data(db_data, freq, param[0], param[1])




