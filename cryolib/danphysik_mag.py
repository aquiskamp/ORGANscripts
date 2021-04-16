__author__ = 'Nikita Kostylev'
__version__ = '20.03.2015_1.0'

import serial
import io
import time
# Module to communicate with DANPHYSIK MAGNET SUPPLY AND GAUSSMETER


def ctoutf(strvar):
    res = str(strvar+"\r\n").encode('utf8')
    return res

def utftoct(strvar):
    res = str(strvar.decode('utf8')).rstrip()
    return res

# mega_port: serial port number, 'COM5'
#
#Returns s: socket object or None if not connected
def connectdan(ser_port):   # Create socket and connect to host
    ser = serial.Serial(ser_port, 9600, timeout=5)
    print("Connected DANPHYSIK to Serial Port:", ser.name)
    print("INITIALISING")
    ser.write(ctoutf("UNLOCK"))
    time.sleep(1)
    ser.write(ctoutf("REM"))
    time.sleep(1)
    ser.write(ctoutf("NASW"))
    ser.write(ctoutf("RS"))
    ser.write(ctoutf("F"))
    time.sleep(4)
    ser.write(ctoutf("RS"))
    time.sleep(1)
    ser.write(ctoutf("WA 0"))
    time.sleep(1)
    ser.write(ctoutf("N"))
    print("DANPHYSIK READY")
    return ser

def connectgauss(ser_port):   # Create socket and connect to host
    ser2 = serial.Serial(ser_port,19200, timeout=5)
    print("Connected GAUSSMETER to Serial Port:", ser2.name)

    ser2.write(ctoutf("#MODE 0"))
    time.sleep(1)
    print(utftoct(ser2.readline()))

    ser2.write(ctoutf("#AUTO 0"))
    time.sleep(1)
    print(utftoct(ser2.readline()))

    ser2.write(ctoutf("#RANGE 6"))
    time.sleep(1)
    print(utftoct(ser2.readline()))

    ser2.write(ctoutf("#UNIT 1"))
    time.sleep(1)
    print(utftoct(ser2.readline()))

    ser2.write(ctoutf("#TEMP 1"))
    print(utftoct(ser2.readline()))

    print("GAUSSMETER READY")

    return ser2



# Set magnet to specified B field
# s: socket object
# field: field value (usually in Tesla, or whatever units set in settings), eg 0.1
def set_field(s, a):

    if (a > 999999) or (a < -999999):
        print("ERROR: MAG FIELD VALUE TOO LARGE")
        return

    if (a >= 0):
        strval = str(a)
        adz = 6 - len(strval)
        for i in range(adz):
            strval = '0' + strval
    else:
        strval = str(-a)
        adz = 6 - len(strval)
        for i in range(adz):
            strval = '0' + strval
        strval = '-' + strval

        print('Setting B to ', strval)


    s.write(ctoutf('WA ' + strval))
    return


def meas_field(s):
    s.write(ctoutf("?MEAS"))
    time.sleep(0.05)
    return utftoct(s.readline())


# Disconnect Socket
# s: socket object
def disconnect(s):
    s.close()
    return