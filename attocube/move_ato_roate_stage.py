__author__ = 'Aaron Quiskamp'

from attocube_usb import ANC300
anc = ANC300()

#anc.step('y',1000,'d')
anc.step('x',1500,'d')

# import pyvisa
#
# rm = pyvisa.ResourceManager()
# print(rm.list_resources())