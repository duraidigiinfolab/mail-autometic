# Email Auto Bot (Cloud Hosted)

This is a complete automation system that runs entirely in the cloud using GitHub Actions. It logs into your Gmail account, uses Gemini AI to classify emails, deletes old spam/OTPs, and sends Telegram notifications for important emails.

Since it runs on GitHub Actions, **your computer does not need to be turned on**.

---

## Features

1. **Smart AI Classification** — Uses Gemini to automatically analyze and categorize incoming emails (OTP, Marketing, Social, Security, Important, etc.).
2. **AI-Driven Deletions** — Automatically cleans up:
   - OTPs & Security emails older than **24 hours**
   - Marketing & Social emails older than **48 hours**
   - All tracked emails older than **30 days** (removed from local DB)
3. **Telegram Notifications** — Instantly alerts you for emails matching keywords: `boss`, `urgent`, `important`, `bank`.
4. **OTP Masking** — Any 4–8 digit OTP numbers are automatically replaced with `*****` in both Telegram messages and the local database. Your OTPs are never stored or sent in plain text.
5. **Duplicate-Safe** — Each processed email UID is tracked in `mail_data.json`. Even if the bot runs late (GitHub Actions can delay scheduled jobs), it will never miss or double-process an email. The IMAP search covers the **last 3 days**.

---

## How It Works

```
GitHub Actions (cron: 1:00 AM IST daily)
        ↓
Fetch new emails from Gmail (last 3 days via IMAP)
        ↓
Send Telegram alert for important emails (with OTP masked)
        ↓
Classify all unclassified emails with Gemini AI
        ↓
Delete old clutter emails based on category & age
        ↓
Save updated mail_data.json back to repo
```

---

## Schedule

The bot runs automatically **every day at 1:00 AM IST** (`30 19 * * *` UTC).

> **Note:** GitHub Actions scheduled workflows may occasionally run a few minutes to a few hours late due to server load. This does **not** affect email coverage — the bot scans the last 3 days of emails and uses a processed-UID database to ensure nothing is missed or duplicated.

---

## Setup Instructions

### 1. Get a Telegram Bot API Key (Free)
1. Open Telegram and search for **BotFather** (blue checkmark).
2. Send `/newbot` and follow the prompts.
3. BotFather will give you a **token** like `1234567890:ABCdefGHI...` → this is your `TELEGRAM_BOT_TOKEN`.
4. Search for **userinfobot** on Telegram, send it any message, and save the ID it replies with → this is your `TELEGRAM_CHAT_ID`.
5. Search for your new bot's username and send `/start` so it can message you.

### 2. Push to GitHub
1. Create a **Private** repository on GitHub.
2. Upload all files (`mail_bot.py`, `requirements.txt`, and the `.github` folder) to the root of the repository.

### 3. Add Your Secrets to GitHub
Go to **Settings → Secrets and variables → Actions** in your repo and add:

| Secret Name | Value |
| :--- | :--- |
| `GMAIL_USER` | Your Gmail address (e.g., `you@gmail.com`) |
| `GMAIL_APP_PASSWORD` | Your 16-character Gmail App Password |
| `TELEGRAM_BOT_TOKEN` | The token from BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram user ID |
| `GEMINI_API_KEY` | Your Gemini API key |

### 4. You're Done!
The bot will now run automatically every day at **1:00 AM IST**, sending Telegram alerts and cleaning up your inbox silently.

> **Run it manually anytime:** Go to the **Actions** tab → **Mail Automation Bot** → **Run workflow**.  
> Manual runs default to **safe mode** (no deletions, no Telegram alerts) unless you set `test_mode` to `false`.

---

## Email Categories

| Category | Auto-Delete After |
| :--- | :--- |
| OTP / Security | 24 hours |
| Marketing / Social | 48 hours |
| Important | Never (kept) |
