# Import smtplib for the actual sending function
import smtplib
# Import the email modules we'll need
from email.mime.text import MIMEText
from email.message import EmailMessage
from jinja2 import Environment, PackageLoader, select_autoescape

#pwd: rcqymdtvkyyouwff

def send_template_email(price_changed_search_result,newListing_search_result,removedListing_search_result):
    """Sends an email using a template."""
    env = Environment(
        loader=PackageLoader('project', 'email_templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('new_site.html')





    html = template.render(content)

    sendEmail(to, subj, template.render(**kwargs))
def sendEmail(sender='jzoudavy@gmail.com', receiver='jzoudavy@gmail.com', subject="New MLS listing detected", content="New MLS listing detected"):
    EMAIL_ADDRESS = 'jzoudavy@gmail.com'
    EMAIL_PASSWORD = 'rcqymdtvkyyouwff'

    preamble=' Hi you MF. \n '

    msg = EmailMessage()
    mailinglist = ['jzoudavy@gmail.com', 'cerf@gmail.com', 'blue@hotmail.com']
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ','.join(mailinglist)
    msg.set_content(preamble+str(content))

# Send the message via our own SMTP server, but don't include the
# envelope header.

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
