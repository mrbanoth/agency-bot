# Run the Bot 24/7 for Free — GitHub Actions

GitHub runs your bot on their servers every day at 9 AM.
Your PC can be off. Completely free. No server to manage.

---

## One-Time Setup (15 minutes)

### 1. Create a GitHub Account
Go to https://github.com → Sign up (free)

### 2. Create a New Private Repository
- Click the **+** button (top right) → New repository
- Name it: `agency-bot` (or anything)
- Set to **Private** (so your code stays yours)
- Click **Create repository**

### 3. Push Your Code to GitHub
Open your terminal in the project folder and run these commands one by one:

```bash
git init
git add .
git commit -m "Initial setup"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/agency-bot.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

### 4. Add Your Secret Keys to GitHub
(This keeps your Gmail password and Groq key safe — never visible in code)

1. Go to your repo on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** — add these 3 secrets:

| Secret Name | Value |
|-------------|-------|
| `GMAIL_ADDRESS` | sandeepnaikb0@gmail.com |
| `GMAIL_APP_PASSWORD` | your 16-char Gmail app password |
| `GROQ_API_KEY` | your free Groq key |

### 5. Enable the Workflow
1. Click the **Actions** tab in your repo
2. If it says "Workflows aren't running" → click **Enable**
3. Done — it will now run automatically every day at 9 AM IST

---

## Run It Manually (anytime)
1. Go to your repo → **Actions** tab
2. Click **Agency Bot — Daily Lead Run**
3. Click **Run workflow** → **Run workflow**
4. Check your email in ~10 minutes

---

## How It Works

```
GitHub server wakes up at 9 AM IST
        ↓
Installs Python + Chrome (takes 2 min)
        ↓
Runs main.py — scrapes Google Maps Hyderabad
        ↓
Audits websites, generates AI pitches
        ↓
Emails YOU at sandeepnaikb0@gmail.com
        ↓
Saves leads.csv as downloadable artifact
        ↓
GitHub server shuts down (costs nothing)
```

---

## Download Your leads.csv After Each Run
1. Go to **Actions** tab → click the latest run
2. Scroll to the bottom → **Artifacts**
3. Download `leads-XXXXX` → open the CSV

---

## Limits (all free)
- GitHub Actions free: **2,000 minutes/month**
- Each run takes ~15 minutes
- That's 133 runs free per month — you only need 30

---

## If You Ever Want to Change the Time
Open `.github/workflows/daily_run.yml` and edit this line:
```yaml
- cron: '30 3 * * *'   # 3:30 AM UTC = 9:00 AM IST
```

Use https://crontab.guru to calculate any time you want.
