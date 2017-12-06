#!/home/fsoares/purchase_planner/PurchaseOrder_Scheduler/bin/python3

# import easyimap
# import imapclient
# import imaplib




# imapper = easyimap.connect('imap.gmail.com', login, password)
# for mail_id in imapper.listids(limit=100):
#     mail = imapper.mail(mail_id)
#     print(mail.from_addr)
#     # print(mail.to)
#     # print(mail.cc)
#     print(mail.title)
#     # print(mail.body)
#     # print(mail.attachments)

# server = imaplib.IMAP4_SSL('imap.gmail.com')
# resp, data = server.login(login, password)
# if resp != "OK":
#     raise IOError("login failed: " + data[0])
# resp, data = server.select("INBOX")
# if resp != "OK":
#     raise IOError("select failed: " + data[0])
# resp, data = server.uid("SEARCH", "NOT DELETED")
# if resp != "OK":
#     raise IOError("search failed: " + data[0])
# # data will look something like: ["1 2 23"]
# messages = [int(m) for m in data[0].split()]
#
# for message in messages:
#     print(message)


import email, getpass, imaplib, os

detach_dir = 'attachments' # directory where to save attachments (default: current)
# user = raw_input("Enter your GMail username:")
# pwd = getpass.getpass("Enter your password: ")

login = 'estoquepulmao@sodanca.com'
password = 'HFZNxaqqs\mq]_YfE9'

# connecting to the gmail imap server
m = imaplib.IMAP4_SSL("imap.gmail.com")
m.login(login, password)
m.select("INBOX") # here you a can choose a mail box like INBOX instead
# use m.list() to get all the mailboxes

resp, items = m.search(None, "ALL") # you could filter using the IMAP rules here (check http://www.example-code.com/csharp/imap-search-critera.asp)
items = items[0].split() # getting the mails id

for emailid in items:
    print(emailid)
    resp, data = m.fetch(emailid, "(RFC822)") # fetching the mail, "`(RFC822)`" means "get the whole stuff", but you can ask for headers only, etc
    email_body = data[0][1] # getting the mail content
    print(email_body)
    mail = email.message_from_string(email_body) # parsing the mail content to get a mail object

    print("["+str(mail["From"])+"] :" + str(mail["Subject"]))

    #Check if any attachments at all
    if mail.get_content_maintype() != 'multipart':
        continue




    # we use walk to create a generator so we can iterate on the parts and forget about the recursive headache
    for part in mail.walk():
        # multipart are just containers, so we skip them
        print(part)
        if part.get_content_maintype() == 'multipart':
            continue

        # is this part an attachment ?
        if part.get('Content-Disposition') is None:
            continue

        # filename = part.get_filename()

        filename = mail["From"] + "_hw1answer"
        print(filename)

        att_path = os.path.join(detach_dir, filename)

        #Check if its already there
        if not os.path.isfile(att_path) :
            # finally write the stuff
            fp = open(att_path, 'wb')
            print('Opening file')
            fp.write(part.get_payload(decode=True))
            fp.close()


# server = imapclient.IMAPClient("imap.gmail.com", ssl=True)
# server.login(login, password)
# server.select_folder("INBOX")
# messages = server.search(['NOT', 'DELETED'])
# messages = server.fetch(messages, ['FLAGS','ENVELOPE', 'BODYSTRUCTURE']) #,  'RFC822.SIZE'])
#
# print(messages.items())
#
# for mid, content in messages.items():
#     bodystructure = content[b'BODYSTRUCTURE']
#     flags = content[b'FLAGS']
#     envelope = content[b'ENVELOPE']
#     print(flags)
#     print(envelope)
#     print(bodystructure)
#     text, attachments = walk_parts(bodystructure, msgid=mid, server=server)
    # print(text)

# for message in mail.messages:
#     print(message)
#
#     if mail.title == 'ESTOQUE EN CVS' and mail.from_addr == '<anyi@solesdelmar.com>':
#         print('DEBUG CONDITIONS MET')
#         for attachment in mail.attachments:
#             try:
#                 f = open("attachments/" + attachment[0], "wb")
#                 f.write(attachment[1])
#                 f.close()
#
#             except Exception as e:
#                 raise
#
#
