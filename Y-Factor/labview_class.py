import win32com.client as win32
from pathlib import Path as p
import win32com.client

host_vi = r'C:\Users\equslab\Desktop\Axion v4 - dev\Axion_v2.1_HOST_hdf5.vi' #path to VI

class LabView():
    def __init__(self,project_path=r'C:\Users\equslab\Desktop\Axion v4 - dev\Axion.lvproj'): #vi path
        self.LabVIEW_Top    = win32com.client.Dispatch("Labview.Application") # opens labview
        self.LabVIEW=self.LabVIEW_Top #init as if there is no project
        self.LabVIEW_Top._FlagAsMethod('OpenProject')
        proj = self.LabVIEW_Top.OpenProject(project_path)
        self.LabVIEW = proj.Application #over ride to project application
        self.VI = proj.Application.getvireference(host_vi)
        self.VI._FlagAsMethod("Call")  # Flag "Call" as Method
        #self.VI.Call()
    def simple_setup(self,fcent,npts,span,nspectra):
        ''''fcent: Centre Freq In Hz
            npts: number of points integer
            span: takes preset value from 0-10 where 0~=50MHz and 1~=25MHz etc
            update_rate: plus/minus button on host vi - sets num of averages
            nspectra: number of consecutive spectra to take before stopping Vi  '''
        self.VI.setcontrolvalue('Centre freq', str(fcent))  # Set centre freq for digitizer
        self.VI.setcontrolvalue('points', npts)
        self.VI.setcontrolvalue('Number of points', npts)
        self.VI.setcontrolvalue('N', str(span))  # set span # takes a value from 0-6
        self.VI.setcontrolvalue('nspectra', nspectra)  # set update rate
        #self.VI.setcontrolvalue('Window select', str(window)) # set window
        #self.VI.Call()

    def save_data(self,save,path):
        ''''save: Bool T/F
            path: where to save file
            span: takes preset value from 0-6
            update_rate: plus/minus button on host vi - sets num of averages from [-4,4]
            nspectra: number of consecutive spectra to take before stopping Vi  '''
        self.VI.setcontrolvalue('Save', save)  # Set centre freq for digitizer
        self.VI.setcontrolvalue('File path', str(path))
        self.VI.setcontrolvalue('Dataset Path', 'FFT')

    def digitize(self):
        self.VI.Call()