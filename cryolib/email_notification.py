__author__ = 'Nikita Kostylev'
__version__ = '20.03.2015_1.0'

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# Module to notify end user of errors via email

# Send Notification email to specified email addresses
# Email addresses in format
# addr = ['me@gmail.com', 'you@yahoo.com']
def send_email(addr):   # Create socket and connect to host
    print("Sending Email Notification...")

    fromaddr = "qdmlab1@gmail.com" # The address of gmail account ot send notification from
    passwd = "51RQfNDtuq&j" # Gmail account Password
    expname = "ORGAN attocube"  # Name of this experiment
    textfile="errormail.txt"    # Plain Text file containing body of notification email message


    toaddr = [fromaddr] # Send original email to yourself for records

    ccaddr = addr # Send email as cc to everyone else

    # Open a plain text file for reading.  For this example, assume that
    # the text file contains only ASCII characters.
    fp = open(textfile, 'r')
    # Create a text/plain message
    msg = MIMEText(fp.read())
    fp.close()

    msg['From'] = fromaddr
    msg['To'] = ', '.join(toaddr)
    msg['Cc'] = ', '.join(ccaddr)

    msg['Subject'] = "CRYO MEASUREMENT FAILURE: [" + expname + "]" # Message Subject

    # Connecting to GMAIL smtp server and sending email message:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(fromaddr, passwd)
    text = msg.as_string()
    res1 = server.sendmail(fromaddr, toaddr+ccaddr, text)
    res2 = server.quit()
    print(res1, res2)
    return


