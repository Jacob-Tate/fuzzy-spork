# @file emailReminder.py
# @author Jacob Tate
# @brief Responds to emails at a given time reminding you the chain is there
#

# Email related packages
import imaplib
import smtplib
import email

# Python libs
import time
import sys
import json
import re
import asyncio

# imported libraries
import pause
import dateparser

# Determine if the command is correctly used
if len(sys.argv) < 2:
	print("Useage: ", sys.argv[0], " <config_file.json>")
	sys.exit()

# if yes open the given config file and populate the fields for later use
with open(sys.argv[1]) as configFile:
	config = json.load(configFile)

senders = []

# Notify's a particular email address of the fact that an email should have been sent
#
# @param username The email to say the alert is coming from
# @param to The email to send the alert to
# @param smtpserver An open SMTP server to send the alert from
def notifyMe(username, to, smtpserver):
    body = ''
    header = 'To: '+to+'\n' + 'From: Auto Responder <'+to+'>\n' + 'Subject: Auto-response sent!\n'
    message = header + '\n' + body + '\n\n'
    smtpserver.sendmail(username, to, message)
 
# Send the email to the client address
#
# @param config the configuration data to use to create the header
# @param to the email address to forward the alert to
# @param subject the subject of the new email 
def sendResponse(config, to, subject):
    smtpserver = smtplib.SMTP("smtp.gmail.com",587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo
    smtpserver.login(config["username"], config["password"])
    header = 'To:' + to + '\n' + 'From: '+config["name"]+' <'+config["fromEmail"]+'>\n' + 'Subject:'+subject+'\n'
    message = header + '\n' + config["responseMessage"] + '\n\n'
    smtpserver.sendmail(config["username"], to, message)
    if "notificationEmail" in config:
        notifyMe(config["username"], config["notificationEmail"], smtpserver)
    smtpserver.close()

# Determines how long to wait and sends the email once the time has come
#
# @param config the configuration data to use to create the header
# @param to the email address to forward the alert to
# @param subject the subject of the new email  
async def send_email(time, config, to, subject):
    regTime = re.search('.*remind (\\S*) (.*)', time)
    time = dateparser.parse(regTime.group(2))
    print("waiting until ", time)
    pause.until(time)
    print("Waiting complete sending reminder!")
    if regTime.group(1) != 'me':
        to = regTime.group(1)
 
    sendResponse(config, to, subject)

# Determines if an email has been recieved
#
# @param config the configuration data to use to create the header
def checkForEmails(config):
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(config["username"], config["password"])
    #mail.list()
    # Out: list of "folders" aka labels in gmail.
    mail.select("inbox") # connect to inbox.
    result, data = mail.uid('search', None, '(HEADER Subject "'+config["searchString"]+'" UNSEEN)') # search and return uids instead
#    print str(result)
#    print str(data)
    if len(data) > 0 and len(data[0]) > 0:
        print("New message found...")
        latest_email_uid = data[0].split()[-1]
        result, data = mail.uid('fetch', latest_email_uid, '(RFC822)')
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)
         
        print(email_message['To'])
     
        sender = email.utils.parseaddr(email_message['From'])
        subject = email_message.get("Subject")
        if sender in senders:
            print("Ignoring claimed email from %s,%s..."%sender)
        elif subject.startswith("Re:"):
            print("Ignoring response email...")
        else:
            print("Sending claim response to:")
            print(sender)
            senders.append(sender)
            asyncio.run(send_email(subject, config, sender[1], "Re: "+subject))
    mail.close()
    mail.logout()
 
   
while True:
    checkForEmails(config)
    time.sleep(10)