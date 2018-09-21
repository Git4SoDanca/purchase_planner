#!/home/fsoares/purchase_planner/PurchaseOrder_Scheduler/bin/python3

import email
import imaplib
import os
import datetime
import configparser
import re
import subprocess

detach_dir = 'attachments' # directory where to save attachments (default: current)

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')

login = config['DEFAULT']['email_login']
password = config['DEFAULT']['email_password']
email_server = config['DEFAULT']['email_imap_server']

prev_date = datetime.datetime.strptime('1970-01-01 00:00:00 -0400','%Y-%m-%d %H:%M:%S %z')

file_list = []
for fn in config['DEFAULT']['email_file_attch_list'].split(','):
    file_list.append(fn.strip())


# connecting to the gmail imap server
m = imaplib.IMAP4_SSL(email_server)
m.login(login, password)
m.select("INBOX") # here you a can choose a mail box like INBOX instead
# use m.list() to get all the mailboxes

resp, items = m.search(None, "ALL") # you could filter using the IMAP rules here (check http://www.example-code.com/csharp/imap-search-critera.asp)
items = items[0].split() # getting the mails id

# print('DEBUG items',items)

for emailid in items:
    # print(emailid)
    resp, data = m.fetch(emailid, "(RFC822)") # fetching the mail, "`(RFC822)`" means "get the whole stuff", but you can ask for headers only, etc
    email_body = data[0][1] # getting the mail content
    # print(email_body)
    mail = email.message_from_bytes(email_body) # parsing the mail content to get a mail object
    # print('DEBUG mail["FROM"]', str(mail["FROM"]))
    mail_from = (re.search('<(.*)>',str(mail["From"]))).group(1)
    # print('DEBUG mail_from',mail_from)
    # print(" DEBUG ["+str(mail["From"])+"] :\n" + str(mail["Subject"]))#'\n\n'+str(mail))

    # print('DEBUG mail["Date"]', mail['Date'])
    email_date =  email.utils.parsedate_to_datetime(mail['Date'])
    # print('DEBUG email_date',email_date)
    extr_domain = mail_from = (re.search('<.*@(.*)>',str(mail["From"]))).group(1)
    # print('DEBUG extr_domain',extr_domain)
    if extr_domain == config['DEFAULT']['source_email_domain'] and prev_date <= email_date:
        #Check if any attachments at all
        if mail.get_content_maintype() != 'multipart':
            continue
        # we use walk to create a generator so we can iterate on the parts and forget about the recursive headache
        for part in mail.walk():
            # multipart are just containers, so we skip them
            # print(part)
            if part.get_content_maintype() == 'multipart':
                continue

            # is this part an attachment ?
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()

            # filename = mail["From"] + "_hw1answer"

            att_path = os.path.join(detach_dir, filename)
            # print('DEBUG check file in list "{0}" "{1}"'.format(filename, filename in file_list))
            if filename in file_list:
                # finally write the stuff
                fp = open(att_path, 'wb')
                print('Opening file')
                fp.write(part.get_payload(decode=True))
                fp.close()

    print('emailid',emailid)
    m.store(emailid, '+FLAGS', '\\Deleted')
