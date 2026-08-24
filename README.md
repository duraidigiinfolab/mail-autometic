# Gmail Auto Bot (Cloud Hosted)

This is a complete automation system that runs completely in the cloud using GitHub Actions. It will automatically log into your Gmail, delete old spam/OTPs, and send you WhatsApp notifications for important emails.

Since it runs on GitHub Actions, **your computer does not need to be turned on**.

## Features
1. **Deletes OTPs** that are older than 24 hours.
2. **Deletes Marketing/Promotional emails** that are older than 48 hours.
3. **Deletes Social Media emails** that are older than 48 hours.
4. **Sends WhatsApp Notifications** for any new Important or Reply emails received in the last 3 hours.

---

## Setup Instructions

### 1. Get a CallMeBot API Key (Free)
We use CallMeBot to send free WhatsApp messages to your phone.
1. Add the phone number `+34 699 15 84 52` to your Phone Contacts (name it CallMeBot).
2. Send the message `I allow callmebot to send me messages` on WhatsApp to that contact.
3. The bot will instantly reply with your `apikey`. Save this key!

### 2. Push to GitHub
1. Create a **Private** repository on your GitHub account.
2. Upload all the files in this folder (`mail_bot.py`, `requirements.txt`, and the `.github` folder) to that repository. 
   *(Make sure the `.github` folder is at the very root of your repository!)*

### 3. Add Your Secrets to GitHub
For security, you must NEVER upload your passwords directly in the code or a `.env` file to GitHub. Instead, we use GitHub Secrets.
1. Go to your GitHub repository in your web browser.
2. Click on **Settings** > **Secrets and variables** > **Actions**.
3. Click the green **New repository secret** button and add these exactly:

| Name | Secret Value |
| :--- | :--- |
| `GMAIL_USER` | Your email (e.g., `you@gmail.com`) |
| `GMAIL_APP_PASSWORD` | The 16-letter App Password you generated earlier |
| `CALLMEBOT_PHONE` | Your full phone number with country code (e.g., `+919876543210`) |
| `CALLMEBOT_API_KEY` | The API key you got in Step 1 |

### 4. You're Done!
The bot is now fully active. It will automatically run:
* **Every 3 hours** to check for new important emails and notify you on WhatsApp.
* While checking, it will also quietly delete any old OTPs and marketing emails in the background.

> **Testing it right now:**
> You don't have to wait 3 hours! You can go to the **Actions** tab in your GitHub repository, click on **Mail Automation Bot** on the left, and click the **Run workflow** button to force it to run immediately.
