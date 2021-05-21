import cryolib.general as gen
import pyvisa
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import vna_single_sweep as vnass


#VNA settings
channel = "1" #VNA Channel Number
warn_email_list = ['21727308@student.uwa.edu.au']
vnass.set_module(channel, warn_email_list) # Reset VNA Module
vnass.establish_connection()    # Establish connection to VNA
sweep_type = "test_DAQ"
