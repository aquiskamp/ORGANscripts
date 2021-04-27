__author__ = 'Nikita Kostylev'
__version__ = '20.03.2015_1.0'

# NOTE: THIS VERSION DOESN'T CONTAIN CLASSES!
# THEREFORE, ONLY ONE VNA CAN BE CONNECTED TO AND CONTROLLED AT A TIME
import time

import cryolib.vna_n5230a_PNA as vna
#import cryolib.vna_N5225A_VNA as vna
#import cryolib.vna_E5061B_ENA as vna
#import cryolib.vna_FFox as vna
#import cryolib.vna_8720ET_VNA as vna

import pyvisa # important for catching of visa errors
import cryolib.email_notification as emailnotif # import email notification module

import warnings
import matplotlib.pyplot as plt


# Individual VNA SETTINGS:

# Set averaging mode:
# ("sweep" for multiple sweeps or
# "point" for point-after-point)
averaging_mode="sweep"


# Other stuff from here

VNA_gpib = ""
device_id = ""
channel = ""
email_notif_list="[]"

# Local Variables
inst = None
old_fcent = None
old_fspan = None
old_bandwidth = None
old_npoints = None
old_power = None


# Reset this VNA module with new gpib address and device name
# new_gpib_address: e.g. "GPIB0::16::INSTR"
# new_device_id: e.g.  "Agilent Technologies,N5225A,MY51451161,A.09.80.20"
# new_channel: channel number, e.g. "1"
# email_notif_list : list of emails in format ['me@gmail.com', 'you@yahoo.com'] to send error notifications to
def set_module(new_channel="1", new_email_notif_list="[]"):
    global VNA_gpib
    VNA_gpib = vna.VNA_gpib
    global device_id
    device_id = vna.VNA_device_id
    global channel
    channel = new_channel
    global email_notif_list
    email_notif_list = new_email_notif_list

    global inst
    inst = None
    global old_fcent
    old_fcent = None
    global old_fspan
    old_fspan = None
    global old_bandwidth
    old_bandwidth = None
    global old_npoints
    old_npoints = None
    global old_naverages
    old_naverages = None
    global old_power
    old_power = None

    return


# Functions
# Connect to vna
def establish_connection():
    global inst
    inst = vna.connect(VNA_gpib, device_id) # establish vna session
    if inst is None:
        exit(1)
    vna.reset(inst) # reset vna
    vna.s21_set_mode(inst, channel) # prepare for s21 measurement
    return


# Disconnect from vna
def close_connection():
    vna.terminate(inst)  # Close connection
    return

def get_dev_id():
    global device_id
    return device_id

def get_maxi():
    maxi = vna.get_max(inst)
    return maxi

def width():
    w = vna.get_width(inst)
    return w
def power_on_off(on_off):
    vna.power_on_off(inst, on_off)
    return

# Do a sweep
# Params: [fcent, fspan, bandwidth, npoints, power]
#
# Returns S21 array as [[real vals], [imag vals]]
def sweep(params):
    fcent = params[0]
    fspan = params[1]
    bandwidth = params[2]
    npoints = params[3]
    naverages = params[4]
    power = params[5]

    for attempt in range(15): # Try communication/measurement with vna 5 times, before giving up
        try:
            global old_power
            if old_power != power:
                vna.set_source_power(inst, power, channel) # Set source power
                old_power = power
            global old_npoints
            if old_npoints != npoints:
                vna.set_point_number(inst, npoints, channel) # Set Number of Points Per Span
                old_npoints = npoints
            global old_bandwidth
            if old_bandwidth != bandwidth:
                vna.set_bandwidth(inst, bandwidth, channel) # Set Bandwidth
                old_bandwidth = bandwidth
            global old_fcent
            if old_fcent != fcent:
                vna.set_fcentral(inst, fcent, channel) # Set Fcent
                old_fcent = fcent
            global old_fspan
            if old_fspan != fspan:
                vna.set_fspan(inst, fspan, channel) # Set Fspan
                old_fspan = fspan
            global old_naverages
            if old_naverages != naverages:
                vna.set_averaging(inst, naverages, averaging_mode, channel)  # Set number of averages
                old_naverages = naverages



            sweep_time = vna.get_sweep_time(inst, channel)
            if averaging_mode == "sweep":
                sweep_time = sweep_time * naverages*1 + 1# If the mode is "sweep", need to account for multiple sweeps
            #sweep_time=299
            print("Freq = %2.2e Hz > Sweep Time = %.1f secs" % (fcent, round(sweep_time, 1)))


            if (sweep_time > 2.0):
                time_step = sweep_time/10
            else:
                time_step = sweep_time

            t = 0.0;

            while (t < sweep_time):
                vna.autoscale(inst) # Autoscale View
                percentage = int(t / sweep_time * 100.0)
                print(percentage)
                print('Progress: [%d%%]\r' % percentage, end="")

                if float(t) > (sweep_time + time_step):
                    warnings.warn("Sweep time exceeded, waiting!..")

                plt.pause(time_step)  # Sleep for a time_step
                #time.sleep(time_step)
                t += time_step


            result = vna.download_complex(inst, channel)  # download complex values

            print("Sweep Complete (" + str(int(result.size / 2)) + " points)")


        except pyvisa.errors.VisaIOError as e:
            warnings.warn("VNA GPIB VisaIOError")
            print('VNA Comm Failed! Err: ', str(e), 'Waiting to flush visa')
            plt.pause(10) # Wait for 10 seconds for vna to catch up?

        else:
            break
    else:
        print('Communication with VNA Aborted -> Send Warning email') # we failed all the attempts - deal with the consequences.
        emailnotif.send_email(email_notif_list)
        raise ValueError("VNA Communication Failure")
        exit(-1)


    return result # Finally, if all goes well - return result of vna sweep
