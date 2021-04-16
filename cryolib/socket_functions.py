__author__ = 'Nikita Kostylev'
__version__ = '20.03.2015_1.0'

# Module to communicate with devices via TCPIP Socket (quite generic module)

import socket # Python 3 compat
import sys

# Connect to TCPIP Server Socket
# am_host: host IP address, eg '130.95.156.154'
# am_port: host port number, eg 7180
#
#Returns s: socket object
def connect_to(am_host, am_port):   # Create socket and connect to host
    HOST = am_host    # The remote host
    PORT = am_port             # The same port as used by the server
    s = None

    for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        try:
            s = socket.socket(af, socktype, proto)
        except socket.error as msg:
            s = None
            continue
        try:
            s.connect(sa)
        except socket.error as msg:
            s.close()
            s = None
            continue
        break

    if s is None:
        print ('could not open socket')
        sys.exit(1)

    return s


# Close TCPIP Socket
# s: socket object to close
def close(s):  # Close socket
    s.close()
    return

# Send a message to TCPIP Server Socket
# s: socket object
# data: message to send, eg. "*IDN?;"
def send_to(s, data):  # Send a message to server
    s.sendall(data.encode())
    return


# Receive/read a single byte from the input buffer
# s: socket object
#
# Returns the byte in ASCII characters
def receive_from_raw(s):     # Receive packet from server
    err_msg = ""

    try:
        data_recv = s.recv(1)
    except socket.error as msg:
        data_recv = None
        err_msg = msg

    if data_recv is None:
        raise ValueError('No answer received:', err_msg)

    else:
        answ=data_recv.decode()

    return answ


# Receive a message string from TCPIP Server
# s: socket object
#
# Pulls a single (eol terminated) message off input buffer and returns it
def receive_from(s):
    answ = ""
    all_response = ""
    eol_sep = '\n'

    while (answ != eol_sep):
        answ = receive_from_raw(s)
        #print(answ)
        all_response += answ

    output = all_response.rstrip()

    return output

# Send a message to/query TCPIP socket and read the reply
# s: socket object
# data: message to send
#
# Returns the replied message
# NOTE: THIS WILL ONLY PULL OFF BUFFER AND RETURN A SIGLE EOL-TERMIATED MESSAGE!
# IF YOUR RETURN MESSAGE HAS MULTIPLE EOLs, CLEAR THE BUFFER WITH receive_from(s)
def query(s, data):
    send_to(s, data)
    answ = receive_from(s)
    return answ