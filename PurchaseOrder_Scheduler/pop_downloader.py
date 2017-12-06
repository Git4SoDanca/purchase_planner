import poplib
import email
import os
import datetime

class GmailTest(object):
    def __init__(self):
        self.savedir="attachments"

    def test_save_attach(self):

        login = 'estoquepulmao@sodanca.com'
        password = 'HFZNxaqqs\mq]_YfE9'

        file_list = ['BA.csv', 'JAZZ.csv', 'SD.csv', 'ZAPATO.csv', 'CONF.csv']

        self.connection = poplib.POP3_SSL('pop.gmail.com', 995)
        self.connection.set_debuglevel(0)
        self.connection.user(login)
        self.connection.pass_(password)

        emails, total_bytes = self.connection.stat()
        print("{0} emails in the inbox, {1} bytes total".format(emails, total_bytes))
        # return in format: (response, ['mesg_num octets', ...], octets)
        msg_list = self.connection.list()
        # print(msg_list)

        goodsubj=''
        goodemail=''
        prev_date = datetime.datetime.strptime('1970-01-01 00:00:00 -0400','%Y-%m-%d %H:%M:%S %z')
        # messages processing
        for i in range(emails):

            # return in format: (response, ['line', ...], octets)
            response = self.connection.retr(i+1)
            raw_message = response[1]

            str_message = email.message_from_bytes(b'\n'.join(raw_message))
            fromstr = str_message['from']
            subjstr = str_message['subject']
            # print('DEBUG fromstr, subjstr', fromstr, subjstr)
            # Mon, 4 Dec 2017 16:58:51 -0400

            email_date = datetime.datetime.strptime(str_message['date'],'%a, %d %b %Y  %H:%M:%S %z')
            # print(i,'DEBUG EMAIL DATE {0}, PREV DATE {1}, FROM {2}, SUBJ "{3}"'.format(email_date, prev_date, fromstr, subjstr))
            # print ('DEBUG CONDITION CHECK 1 subj',subjstr == 'ESTOQUE EN CVS')
            # print ('DEBUG CONDITION CHECK 2 from',fromstr == '<anyi@solesdelmar.com>')
            # print ('DEBUG CONDITION CHECK 3 date',prev_date < email_date)


            if fromstr[-17:] == '@solesdelmar.com>' and prev_date <= email_date:
                # goodemail = fromstr
                # goodsubj = subjstr
                # print('\n\nDEBUG prev_date, email_date', prev_date, email_date)
                # print('DEBUG IF CHECK',prev_date < email_date)
                # if prev_date < email_date:
                #     print('DEBUG IF')

                # save attach

                for part in str_message.walk():
                    print(part.get_content_type())

                    if part.get_content_maintype() == 'multipart':
                        continue

                    if part.get('Content-Disposition') is None:
                        print("no content dispo")
                        continue

                    filename = part.get_filename()
                    if not(filename): filename = "test.txt"
                    # print(filename)

                    if filename in file_list:

                        prev_date = email_date
                        fp = open(os.path.join(self.savedir, filename), 'wb')
                        fp.write(part.get_payload(decode=1))
                        fp.close

                else:
                    # print('ELSE')
                    pass
        #I  exit here instead of pop3lib quit to make sure the message doesn't get removed in gmail
        self.connection.quit()
        import sys
        sys.exit(0)

d=GmailTest()
d.test_save_attach()
