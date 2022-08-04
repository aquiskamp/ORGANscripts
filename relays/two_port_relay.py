import subprocess

def relay_on_off(open_close,number,serial='HURTM'):
        subprocess.Popen(r'C:\Users\QDM\Desktop\Aaron\ORGANscripts\relays\CommandApp_USBRelay ' + serial + ' ' + open_close + ' ' + number)