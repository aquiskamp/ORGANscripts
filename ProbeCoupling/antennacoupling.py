
import gather_data as gd
import cryolib.general as gen


#params = gd.input_popup()
#gd.gather_data(params, True)



path = r"C:\Users\deepa\PycharmProjects\pythonProject\Deepali_single_sweep_010.hdf5"
freq, vna, param = gd.read_h5_file(path)
db_data = gen.complex_to_dB(vna)


gd.present_data(db_data, freq, param[0], param[1])




