# Agency Bot — Start Here

## STEP 1 — Run Setup (one time only)
Double-click `setup.bat`
This installs Python packages + headless Chrome. Takes ~3 minutes.

---

## STEP 2 — Get Your 2 Free Keys (takes 5 minutes)

### A) Gmail App Password (for email notifications to yourself)
1. Go to **myaccount.google.com**
2. Security → 2-Step Verification → Turn ON
3. Search **"App passwords"** on the same page
4. Name it `AgencyBot` → click Create
5. Copy the 16-character password shown
6. Open `.env` → paste after `GMAIL_APP_PASSWORD=`

### B) Groq API Key (free AI pitch generator)
1. Go to **https://console.groq.com**
2. Sign up with your Google account (free, no credit card)
3. Click **API Keys** → Create Key
4. Copy the key
5. Open `.env` → paste after `GROQ_API_KEY=`

Your `.env` should look like:
```
GMAIL_ADDRESS=sandeepnaikb0@gmail.com
GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
TARGET_CITY=Hyderabad
```

---

## STEP 3 — Start the Bot

**Run once (test it):**
```
venv\Scripts\activate
python main.py
```

**Run 24/7 (keeps running every day at 9 AM):**
Double-click `run_24_7.bat` → keep the window open

---

## What Happens Automatically

```
Every day at 9 AM:
  1. Bot searches Google Maps for 10 business types in Hyderabad
  2. Audits each website (speed, mobile, SSL, SEO)
  3. Scores them — HIGH / MEDIUM / SKIP
  4. Generates a personalised 3-point pitch for each hot lead
  5. Saves all leads to leads.csv
  6. Emails YOU at sandeepnaikb0@gmail.com with a full digest
```

You wake up, check your email, pick the best leads, send the pitch manually.

---

## Files in This Folder

| File | What it does |
|------|-------------|
| `config.py` | Your settings (name, city, etc.) |
| `.env` | Your secret keys (Gmail, Groq) |
| `main.py` | Full pipeline — run this |
| `scheduler.py` | 24/7 loop — calls main.py daily |
| `pitch_engine.py` | AI pitch generator (Groq) |
| `notifier.py` | Sends email digest to you |
| `leads.csv` | All leads collected so far |
| `agency_log.txt` | Log of everything the bot did |
| `setup.bat` | One-time setup |
| `run_24_7.bat` | Start the daily scheduler |
| `outreach_templates.md` | Copy-paste messages to send manually |

---

## No Money Needed — Everything is Free
- **Groq AI**: Free tier — 14,400 requests/day
- **Gmail SMTP**: Free — uses your existing Gmail
- **Google Maps scraping**: Free — Playwright browser
- **Python + schedule**: Free — open source
