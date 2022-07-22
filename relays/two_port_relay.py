import subprocess

def relay_on_off(serial='HURTM',open_close,number):
        subprocess.Popen(r'C:\Users\QDM\Desktop\Aaron\ORGANscripts\relays\CommandApp_USBRelay ' + serial + ' ' + open_close + ' ' number)