import subprocess
from pathlib import Path as p

full_filename = p.home()/p('Desktop/ORGAN_15GHz/test.h5')

subprocess.Popen(r"cd C:\Users\equslab\AppData\Local\Programs\Python\Python38-32& python Digitize_labview32.py " + str(full_filename),shell=True)
#subprocess.run(r'python Digitize_labview32.py', shell=True)
