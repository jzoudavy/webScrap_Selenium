# Import smtplib for the actual sending function
import smtplib
# Import the email modules we'll need
from email.mime.text import MIMEText
from email.message import EmailMessage



def sendEmail(sender='jzoudavy@gmail.com', receiver='jzoudavy@gmail.com', subject="New MLS listing detected", content="New MLS listing detected"):
    preamble=' Hi you MF. \n '

    msg = EmailMessage()
    mailinglist = ['jzoudavy@gmail.com', 'cerf@gmail.com', 'blue@hotmail.com']
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ','.join(mailinglist)
    msg.set_content(preamble+str(content))

# Send the message via our own SMTP server, but don't include the
# envelope header.
    s = smtplib.SMTP('localhost:1025')
    s.send_message(msg)
    s.quit()