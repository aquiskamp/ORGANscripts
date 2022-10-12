import win32com.client as win32
from pathlib import Path as p
import win32com.client

host_vi = r'C:\Users\equslab\Desktop\Axion v4_aaron\Axion_v2.0_HOST.vi' #path to VI

class LabView():
    def __init__(self,project_path=r'C:\Users\equslab\Desktop\Axion v4_aaron\Axion.lvproj'): #vi path
        self.LabVIEW_Top    = win32com.client.Dispatch("Labview.Application") # opens labview
        self.LabVIEW=self.LabVIEW_Top #init as if there is no project
        self.LabVIEW_Top._FlagAsMethod('OpenProject')
        proj=self.LabVIEW_Top.OpenProject(project_path)
        self.LabVIEW = proj.Application #over ride to project application
        self.VI = proj.Application.getvireference(host_vi)
        self.VI._FlagAsMethod("Call")  # Flag "Call" as Method
        #self.VI.Call()

    def simple_setup(self,fcent,npts,span,update_rate,window):
        self.VI.setcontrolvalue('Centre freq', str(fcent))  # Set centre freq for digitizer
        self.VI.setcontrolvalue('points', npts)
        self.VI.setcontrolvalue('N', str(span))  # set span # takes a value from 0-6
        self.VI.setcontrolvalue('speed', update_rate)  # set update rate
        self.VI.setcontrolvalue('Window select', str(window)) # set window


