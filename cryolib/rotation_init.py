import pyvisa as visa
import time
import numpy as np
from zaber_motion import Library
from zaber_motion.ascii import Connection
from zaber_motion import Units
from zaber_motion import Measurement

def zaber_init():

# initialise pyVisa resource manager
    rm = visa.ResourceManager()

    # prints list of connected resources
    print(rm.list_resources())
    code = rm.list_resources()[0]

# ----- Turntable initialisation -----
    Library.enable_device_db_store()
    turnTableUSB = "COM5"
    initial_pos = 80.75

    with Connection.open_serial_port(turnTableUSB) as connection:
        # Scan for devices on USB port
        device_list = connection.detect_devices()
        print("Devices found:", device_list)
        # select first device
        device = device_list[0]

        # get device's axis
        axis = device.get_axis(1)

    return axis

#def move_absolute(position):
#    rot_init = axis.prepare_command("home")

#    axis.generic_command(rot_init)


#def reset_position(theta_stop):
#    move_rel(-theta_stop)


def move_rel(theta,axis):
    rotation = axis.prepare_command("move rel ?", Measurement(value=theta, unit=Units.ANGLE_DEGREES))

    axis.generic_command(rotation)


def move_steps(start, stop, step):
    temp = start
    move_rel(temp)
    print("Measure at " + str(temp) + " degrees")

    no_steps = int((stop - start) / step)

    for x in range(no_steps):
        time.sleep(2)
        temp += step
        move_rel(step)
        print("Measure at " + str(temp) + " degrees")

    print("Finished Reading")
    time.sleep(2)
    move_rel(-stop)


# with Connection.open_serial_port(turnTableUSB) as connection:
#     # Scan for devices on USB port
#     device_list = connection.detect_devices()
#     print("Devices found:", device_list)
#     # select first device
#     device = device_list[-1]
#
#     # get device's axis
#     axis = device.get_axis(1)
#
#     # go to origin
#     #reset_position()
#     #time.sleep(2)
#     print("Ready to move")
#     move_steps(0, 200, 50)