import imaplib
import email
import os
import json
import time
import requests
import datetime
import schedule
from email.header import decode_header
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import types

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
DATA_FILE = "mail_data.json"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

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
        print(f"[TEST MODE] Telegram:\n{message}")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def get_imap_connection():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        mail.select("inbox")
        return mail
    except Exception as e:
        print(f"IMAP Login failed: {e}")
        return None

def fetch_new_emails():
    print("Fetching new emails...")
    mail = get_imap_connection()
    if not mail: return
    
    data = load_data()
    now = datetime.datetime.now(datetime.timezone.utc)
    
    date_3d_ago = (datetime.date.today() - datetime.timedelta(days=3)).strftime("%d-%b-%Y")
    status, messages = mail.uid('search', None, f"SINCE {date_3d_ago}")
    
    if status != "OK" or not messages[0]:
        print("No recent emails found.")
        mail.logout()
        return

    uid_list = messages[0].split()
    new_emails = 0

    for e_uid in uid_list:
        e_uid_str = e_uid.decode('utf-8')
        if e_uid_str in data:
            continue
            
        res, msg_data = mail.uid('fetch', e_uid, '(RFC822)')
        if res != "OK": continue
            
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                date_tuple = email.utils.parsedate_tz(msg.get("Date"))
                if not date_tuple: continue
                    
                msg_timestamp = email.utils.mktime_tz(date_tuple)
                msg_date = datetime.datetime.fromtimestamp(msg_timestamp, datetime.timezone.utc)
                
                subject = decode_subject(msg.get("Subject", ""))
                sender = decode_subject(msg.get("From", ""))
                
                body = get_email_body(msg)
                snippet = body[:300].replace('\n', ' ').replace('\r', '')
                
                data[e_uid_str] = {
                    "timestamp": msg_timestamp,
                    "date_str": str(msg_date),
                    "sender": sender,
                    "subject": subject,
                    "snippet": snippet,
                    "status": "UNCLASSIFIED",
                    "category": None
                }
                new_emails += 1
                
                # Instant notification for potentially important senders (optional, simple keyword check)
                if any(k in sender.lower() or k in subject.lower() for k in ["boss", "urgent", "important", "bank"]):
                    send_telegram_message(f"🔔 *Important Alert*\n\n*From:* {sender}\n*Subject:* {subject}\n\n{snippet[:100]}...")

    save_data(data)
    mail.logout()
    print(f"Added {new_emails} new emails to local DB.")

def classify_emails_with_ai():
    if not client:
        print("Gemini API not configured.")
        return
        
    data = load_data()
    unclassified = {uid: m for uid, m in data.items() if m.get("status") == "UNCLASSIFIED"}
    
    if not unclassified:
        print("No new emails to classify.")
        return
        
    print(f"Batch classifying {len(unclassified)} emails with Gemini...")
    
    # Build a giant prompt string
    batch_text = "Emails to classify:\n\n"
    for uid, m in unclassified.items():
        batch_text += f"ID: {uid}\nSender: {m['sender']}\nSubject: {m['subject']}\nSnippet: {m['snippet']}\n\n"
        
    system_prompt = """
You are an expert email assistant. You will be provided with a batch of emails.
For EVERY email provided, you must output a JSON array of objects classifying them and deciding if they should be TRASHED or KEPT.

Categories:
- "OTP" (Any one-time passwords, login codes, verification codes)
- "Security" (Password changed, new login detected)
- "Marketing" (Newsletters, promotional offers, sales, spammy marketing)
- "Social" (Facebook, Twitter, LinkedIn notifications)
- "Important" (Work emails, personal conversations, bills, receipts, flights, banks)

Return strictly a JSON ARRAY:
[
  {
    "id": "THE_ID_PROVIDED",
    "category": "Marketing",
    "decision": "TRASH" // Or "KEEP"
  }
]
"""

    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=batch_text,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        
        result = json.loads(response.text)
        if isinstance(result, dict) and "id" in result:
            result = [result]
            
        classified_count = 0
        for item in result:
            uid = str(item.get("id"))
            cat = item.get("category")
            decision = item.get("decision", "KEEP")
            if uid in data:
                data[uid]["category"] = cat
                data[uid]["decision"] = decision
                data[uid]["status"] = "CLASSIFIED"
                classified_count += 1
                
        save_data(data)
        print(f"Successfully classified {classified_count} emails.")
        
    except Exception as e:
        print(f"Error classifying emails: {e}")

def process_deletions():
    print("Processing time-based deletions...")
    data = load_data()
    mail = get_imap_connection()
    if not mail: return
    
    now_ts = datetime.datetime.now(datetime.timezone.utc).timestamp()
    
    uids_to_trash = []
    keys_to_delete = []
    
    for uid, m in list(data.items()):
        status = m.get("status")
        cat = m.get("category")
        decision = m.get("decision", "KEEP")
        age_hours = (now_ts - m.get("timestamp", 0)) / 3600.0
        
        # 1. 7-day auto cleanup from JSON (168 hours)
        if age_hours > 168:
            keys_to_delete.append(uid)
            continue
            
        if status != "CLASSIFIED":
            continue
            
        # 2. Check AI decision and apply time delays
        should_delete = False
        if decision == "TRASH":
            if cat in ["OTP", "Security", "Verification"]:
                if age_hours > 24:
                    should_delete = True
            elif cat in ["Marketing", "Social"]:
                if age_hours > 48:
                    should_delete = True
            else:
                # If AI says TRASH for anything else, do it after 48h to be safe
                if age_hours > 48:
                    should_delete = True
            
        if should_delete:
            uids_to_trash.append(uid)
            keys_to_delete.append(uid)
            
    if uids_to_trash:
        print(f"Found {len(uids_to_trash)} old categorized emails to trash.")
        if not TEST_MODE:
            chunk_size = 500
            for i in range(0, len(uids_to_trash), chunk_size):
                chunk = [uid.encode('utf-8') for uid in uids_to_trash[i:i + chunk_size]]
                chunk_str = b','.join(chunk)
                
                try:
                    mail.uid('COPY', chunk_str, '[Gmail]/Trash')
                except:
                    try: mail.uid('COPY', chunk_str, '[Gmail]/Bin')
                    except: pass
                
                mail.uid('STORE', chunk_str, '+FLAGS', '\\Deleted')
            mail.expunge()
            send_telegram_message(f"🗑️ *Auto-Cleanup*\nDeleted {len(uids_to_trash)} old clutter emails from your inbox.")
        else:
            print("[TEST MODE] Skipped deletion.")

    # Remove from JSON
    for k in keys_to_delete:
        if k in data:
            del data[k]
            
    save_data(data)
    mail.logout()
    print("Deletion processing complete.")

def run_pipeline():
    print(f"--- Running Pipeline at {datetime.datetime.now()} ---")
    fetch_new_emails()
    process_deletions()

def run_daily_ai():
    print(f"--- Running Daily AI Batch at {datetime.datetime.now()} ---")
    classify_emails_with_ai()
    # Immediately process deletions after classifying
    process_deletions()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--fetch":
            run_pipeline()
        elif sys.argv[1] == "--ai":
            run_daily_ai()
        sys.exit(0)
        
    print("MailAuto is running in background...")
    
    # Run fetch + cleanup every 2 hours
    schedule.every(2).hours.do(run_pipeline)
    
    # Run the expensive AI Batch once a day at midnight
    schedule.every().day.at("00:00").do(run_daily_ai)
    
    # Run once on startup
    run_pipeline()
    run_daily_ai()
    
    while True:
        schedule.run_pending()
        time.sleep(60)
