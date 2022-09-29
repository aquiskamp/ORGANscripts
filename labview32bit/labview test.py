import win32com.client as win32
from pathlib import Path as p
import win32com.client

vi_file = r'C:\Users\equslab\Desktop\Axion v4_aaron\Axion_v2.0_HOST.vi' #path to VI
save_dir = str(p.home()/'Desktop/xcorr_test.hdf5')
digi_fc = 40000000

class LabView():
    def __init__(self,project_path=r'C:\Users\equslab\Desktop\Axion v4_aaron\Axion.lvproj'): #vi path
        self.LabVIEW_Top    = win32com.client.Dispatch("Labview.Application") # opens labview
        self.LabVIEW=self.LabVIEW_Top #init as if there is no project
        self.LabVIEW_Top._FlagAsMethod('OpenProject')
        proj=self.LabVIEW_Top.OpenProject(project_path)
        self.LabVIEW=proj.Application #over ride to project application
        self.VI = proj.Application.getvireference(vi_file)
        self.VI.setcontrolvalue('Centre freq', str(digi_fc))  # Set centre freq for digitizer
        self.VI.setcontrolvalue('N', str(2))  # set span
        self.VI._FlagAsMethod("Call")  # Flag "Call" as Method
        self.VI.Call()


LabView()

import time
time.sleep(100)

VI = None  # remove reference
