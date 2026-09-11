import imaplib
import email
import os
import datetime
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def test_fetch():
    print(f"Logging into {GMAIL_USER}...")
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    mail.select("inbox")
    
    date_3d_ago = (datetime.date.today() - datetime.timedelta(days=3)).strftime("%d-%b-%Y")
    print(f"Searching for emails SINCE {date_3d_ago}...")
    
    status, messages = mail.uid('search', None, f"SINCE {date_3d_ago}")
    if status != "OK" or not messages[0]:
        print("No recent emails found.")
        return
        
    uid_list = messages[0].split()
    print(f"Found {len(uid_list)} emails. Fetching the last 3...")
    
    for e_uid in uid_list[-3:]:
        res, msg_data = mail.uid('fetch', e_uid, '(RFC822)')
        if res != "OK": continue
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg.get("Subject", ""))[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8", errors='ignore')
                print(f"- Subject: {subject}")

if __name__ == "__main__":
    test_fetch()
