__author__ = 'Aaron Quiskamp'

from attocube_usb import ANC300
anc = ANC300()
anc.V({'x':50})
anc.step('x',200,'d')
#anc.step('x',5000,'d')

# import pyvisa
#
# rm = pyvisa.ResourceManager()
# print(rm.list_resources())