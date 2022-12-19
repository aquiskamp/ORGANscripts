from labview_class import LabView
lv = LabView()

'''It is a good idea to calibrate the fpga before use (both offset and scale calibration)
    -- Number of averages needs to be set on the host Vi (ie update rate) before starting script'''

fcent = 25e6
npts = 6553
span = 0 #25MHz approx (uses sliding bar)
nspectra = 5 # how many spectrums to take
#save_path = str(save_dir/exp_name/(str(temp)+'.hdf5'))

#lv.simple_setup(fcent,npts,span,nspectra)
#lv.save_data(True,save_path) # set save directory
lv.digitize()