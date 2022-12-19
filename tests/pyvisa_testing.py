import pyvisa
from tqdm import tqdm

rm = pyvisa.ResourceManager()
VNA_gpib = 'TCPIP0::EMS-40070::hislip_PXI10_CHASSIS2_SLOT1_INDEX0::INSTR'

print(rm.list_resources())

#inst = rm.open_resource(VNA_gpib)  # Connect to resource

#resp = inst.query("*IDN?")  # Check device ID
#print("Connected to Device ID = " + resp)

#inst.write("*RST")  # Full device reset
# all_ids = list(rm.list_resources())
#
# for id in tqdm(all_ids):
#     try:
#         inst = rm.open_resource(id)  # Connect to resource
#         inst.write("*RST")  # Full device reset
#     except:
#         None

