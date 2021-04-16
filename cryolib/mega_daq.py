__author__ = 'Nikita Kostylev'
__version__ = '20.03.2015_1.0'

import serial
import io
# Module to communicate with MEGA DAQ DAC

# mega_port: serial port number, eg 2 for COM3
#
#Returns s: socket object or None if not connected
def connect(mega_port):   # Create socket and connect to host
    ser = serial.Serial(mega_port)
    print("Connected to Serial Port:", ser.name)

    return ser


# Set magnet to specified B field
# s: socket object
# field: field value (usually in Tesla, or whatever units set in settings), eg 0.1
def set_field(s, field):
    s.write(str('SVOL:' + str(field) + ';').encode('utf8'))
    return



# Disconnect Socket
# s: socket object
def disconnect(s):
    s.close()
    return