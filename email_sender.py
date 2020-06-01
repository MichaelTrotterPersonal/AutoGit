import smtplib, ssl
from datetime import datetime
from datetime import time 
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
import sys

port = 465  # For SSL
host = "smtp.gmail.com"
password = "****"
sender_email = "****@gmail.com"



def send_email(to, subject, content):
	""" Send a simple, stupid, text, UTF-8 mail in Python """
	content += "\n\nReply to this email for any questions/complaints/compliments"
	for ill in [ "\n", "\r" ]:
		subject = subject.replace(ill, ' ')

	headers = {
		'Content-Type': 'text/html; charset=utf-8',
		'Content-Disposition': 'inline',
		'Content-Transfer-Encoding': '8bit',
		'From': sender_email,
		'To': to,
		'Date': datetime.now().strftime('%a, %d %b %Y  %H:%M:%S %Z'),
		'X-Mailer': 'python',
		'Subject': subject
		}

	# create the message
	msg = ''
	for key, value in headers.items():
		msg += "%s: %s\n" % (key, value)

	# add contents
	msg += "\n%s\n"  % (content)

	# Create a secure SSL context
	context = ssl.create_default_context()

	with smtplib.SMTP_SSL(host, port, context=context) as server:
		server.login(sender_email, password)

		server.sendmail(headers['From'], headers['To'], msg.encode("utf8"))

	print('email sent')



send_email("****@gmail.com", "test", "test content!")
