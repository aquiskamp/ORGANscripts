__author__ = 'Nikita Kostylev'
__version__ = '20.03.2015_1.0'

import cryolib.socket_functions as am_sock
# Module to communicate with American Magnetics via TCPIP Socket

# Connect to TCPIP Server Socket
# am_host: host IP address, eg '130.95.156.154'
# am_port: host port number, eg 7180
# device_id: device id string, eg "AMERICAN MAGNETICS INC.,MODEL 430,1.62"
#
#Returns s: socket object or None if not connected
def connect(am_host, am_port, device_id):   # Create socket and connect to host
    s = am_sock.connect_to(am_host, am_port)
    s.settimeout(7.0)  # Set answer wait timeout in seconds

    am_sock.receive_from(s) # read the welcome message
    am_sock.receive_from(s) # read the welcome message

    resp = am_sock.query(s, "*IDN?;") # Check device ID
    print("Connected to Device ID = " + resp)

    if resp != device_id:
        am_sock.close(s)
        s = None
        raise ValueError("Incorrect Device ID")


    return s


# Set magnet to specified B field
# s: socket object
# field: field value (usually in Tesla, or whatever units set in settings), eg 0.1
def set_field(s, field):
    am_sock.send_to(s, 'CONFigure:FIELD:TARGet ' + str(field) + ';')
    return

# Check the current state of device
# s: socket object
# returns:
# 1 RAMPING to target field/current
# 2 HOLDING at the target field/current
# 3 PAUSED
# 4 Ramping in MANUAL UP mode
# 5 Ramping in MANUAL DOWN mode
# 6 ZEROING CURRENT (in progress)
# 7 Quench detected
# 8 At ZERO current
# 9 Heating persistent switch
# 10 Cooling persistent switch
def state(s):
    return int(str(am_sock.query(s, 'STATE?;')))


# Get the current field
# s: socket object
# returns the current field value
def get_field(s):
    return am_sock.query(s, 'FIELD:MAGnet?;')


# Disconnect Socket
# s: socket object
def disconnect(s):
    am_sock.close(s)
    return