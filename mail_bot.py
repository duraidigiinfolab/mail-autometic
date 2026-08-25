import imaplib
import email
import os
import requests
import datetime
from email.header import decode_header
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# For local testing, set this to True to prevent actual deletions and Telegram messages
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

def decode_subject(subject_bytes):
    try:
        decoded_subject, encoding = decode_header(subject_bytes)[0]
        if isinstance(decoded_subject, bytes):
            return decoded_subject.decode(encoding or "utf-8", errors='ignore')
        return decoded_subject
    except Exception:
        return str(subject_bytes)

def get_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='ignore')
                except:
                    pass
    else:
        try:
            return msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='ignore')
        except:
            pass
    return "Could not extract body."

def send_telegram_message(message):
    if TEST_MODE:
        print(f"[TEST MODE] Would send Telegram message:\n{message}")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Telegram notification sent successfully.")
        else:
            print(f"Failed to send Telegram notification. HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def delete_emails(mail, query, description):
    print(f"\nSearching for {description}...")
    status, messages = mail.search(None, 'X-GM-RAW', query)
    
    if status != "OK" or not messages[0]:
        print(f"No emails found for {description}.")
        return

    email_ids = messages[0].split()
    print(f"Found {len(email_ids)} emails to delete.")

    if TEST_MODE:
        print(f"[TEST MODE] Skipping deletion of {len(email_ids)} emails.")
        return

    chunk_size = 500
    for i in range(0, len(email_ids), chunk_size):
        chunk = email_ids[i:i + chunk_size]
        chunk_ids = b','.join(chunk)
        
        # Copy to Trash folder first, then mark original as deleted so they actually move to Trash
        try:
            mail.copy(chunk_ids, '[Gmail]/Trash')
        except:
            # Fallback for some localized Gmail accounts (like Bin)
            try:
                mail.copy(chunk_ids, '[Gmail]/Bin')
            except:
                pass
                
        mail.store(chunk_ids, '+FLAGS', '\\Deleted')
    
    print(f"Moved {len(email_ids)} emails to Trash.")

def process_deletions(mail):
    print("--- STARTING DELETION TASKS ---")
    # 1. OTPs older than 1 day
    delete_emails(mail, 'subject:(OTP OR "verification code" OR "one time password" OR "security code") older_than:1d', "OTPs older than 24 hours")
    
    # 2. Marketing/Promotions older than 2 days
    delete_emails(mail, 'category:promotions older_than:2d', "Marketing emails older than 48 hours")
    
    # 3. Social media older than 2 days
    delete_emails(mail, 'category:social older_than:2d', "Social media emails older than 48 hours")
    
    if not TEST_MODE:
        mail.expunge()

def check_important_emails(mail):
    print("\n--- STARTING NOTIFICATION TASKS ---")
    
    # Fetch all emails received in the last day
    query = 'newer_than:1d'
    status, messages = mail.search(None, 'X-GM-RAW', query.encode('utf-8'))
    
    if status != "OK" or not messages[0]:
        print("No new important or reply emails found.")
        return

    email_ids = messages[0].split()
    print(f"Found {len(email_ids)} candidate emails. Filtering for those received in the last 3 hours...")
    
    now = datetime.datetime.now(datetime.timezone.utc)
    notified_count = 0

    for e_id in email_ids:
        # Fetch header and body
        res, msg_data = mail.fetch(e_id, '(RFC822)')
        if res != "OK":
            continue
            
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                # Check date
                date_tuple = email.utils.parsedate_tz(msg.get("Date"))
                if not date_tuple:
                    continue
                    
                msg_timestamp = email.utils.mktime_tz(date_tuple)
                msg_date = datetime.datetime.fromtimestamp(msg_timestamp, datetime.timezone.utc)
                
                time_diff = now - msg_date
                
                # If the email is older than 3 hours (10800 seconds), skip it
                if time_diff.total_seconds() > 10800:
                    continue
                
                subject = decode_subject(msg.get("Subject", ""))
                sender = decode_subject(msg.get("From", ""))
                date_str = msg.get("Date", "")
                
                # Extract a short snippet of the body
                body = get_email_body(msg)
                snippet = body[:200].replace('\n', ' ').replace('\r', '') + ("..." if len(body) > 200 else "")
                
                # Format Telegram message
                telegram_msg = (
                    f"🔔 *New Email*\n\n"
                    f"*From:* {sender}\n"
                    f"*Date:* {date_str}\n"
                    f"*Subject:* {subject}\n\n"
                    f"{snippet}"
                )
                
                send_telegram_message(telegram_msg)
                notified_count += 1

    print(f"Sent {notified_count} Telegram notifications.")

def main():
    if not all([GMAIL_USER, GMAIL_APP_PASSWORD, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        print("ERROR: Missing environment variables. Please check your .env file or GitHub Secrets.")
        return

    print("Connecting to Gmail...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    except Exception as e:
        print(f"Login failed: {e}")
        return

    mail.select("inbox")

    process_deletions(mail)
    check_important_emails(mail)

    mail.close()
    mail.logout()
    print("Done.")

if __name__ == "__main__":
    main()
