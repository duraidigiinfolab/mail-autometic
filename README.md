# Email Auto Bot (Cloud Hosted)

This is a complete automation system that runs completely in the cloud using GitHub Actions. It logs into your Gmail account, uses Gemini to classify emails, deletes old spam/OTPs, and sends Telegram notifications for important emails.

Since it runs on GitHub Actions, **your computer does not need to be turned on**.

## Features
1. **Smart AI Classification**: Uses Gemini to automatically analyze and categorize your incoming emails (OTP, Marketing, Social, Important, etc.).
2. **AI-Driven Deletions**: Gemini determines the category and whether an email is safe to delete. The bot then automatically cleans up OTPs older than 24 hours, and Marketing/Social emails older than 48 hours.
3. **Sends Telegram Notifications** for emails matching keywords (boss, urgent, important, bank).

---

## Setup Instructions

### 1. Get a Telegram Bot API Key (Free)
We use Telegram to send free notifications to your phone. It is very reliable.
1. Open Telegram and search for **BotFather** (it has a blue checkmark).
2. Send the message `/newbot` and follow the prompts to give your bot a name and username.
3. BotFather will give you a **token** (it looks like `1234567890:ABCdefGHI...`). Save this! This is your `TELEGRAM_BOT_TOKEN`.
4. Now, search for **userinfobot** on Telegram. Send it any message. It will reply with your ID number. Save this! This is your `TELEGRAM_CHAT_ID`.
5. Finally, search for the username of the bot you just created in Step 2, and send it the message `/start` so it is allowed to message you.

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
| `GMAIL_USER` | Your Gmail address (e.g., `you@gmail.com`) |
| `GMAIL_APP_PASSWORD` | The 16-letter Gmail App Password |
| `TELEGRAM_BOT_TOKEN` | The Bot Token you got from BotFather |
| `TELEGRAM_CHAT_ID` | The ID number you got from userinfobot |
| `GEMINI_API_KEY` | Your Gemini API key for email classification |

### 4. You're Done!
The bot is now fully active. It will automatically run:
* **Once a day at 7:30 AM IST** to check for new important emails and notify you on Telegram.
* While checking, it will also quietly delete any old OTPs and marketing emails in the background.

> **Testing it right now:**
> You don't have to wait for the daily run! You can go to the **Actions** tab in your GitHub repository, click on **Mail Automation Bot** on the left, and click the **Run workflow** button to force it to run immediately.
