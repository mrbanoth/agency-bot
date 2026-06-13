"""
outreach_sender.py
Automatically sends personalised cold emails to hot leads via Gmail.
- Max 20/day to keep Gmail safe
- Tracks every send in sent_log.csv — no duplicates ever
- Skips anyone who replied "not interested"
"""

import sys, csv, os, time, smtplib, ssl, random
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from config import (
    GMAIL_ADDRESS, GMAIL_APP_PASSWORD,
    YOUR_NAME, YOUR_PHONE, YOUR_PORTFOLIO,
)

SENT_LOG    = "sent_log.csv"
OPT_OUT_LOG = "optout_log.csv"
DAILY_LIMIT = 20


def _build_email(lead: dict) -> tuple:
    name     = lead.get("name", "Team")
    issues   = [i.strip() for i in lead.get("website_issues","").split("|") if i.strip()]
    top3     = issues[:3]
    has_site = bool(lead.get("website","").strip())
    category = lead.get("category","business")
    city     = lead.get("city","your city")

    if not has_site:
        subject = f"Quick question about {name}'s online presence"
        body = f"""Hi {name},

I was searching for {category} services in {city} on Google and couldn't find {name} online.

You're likely getting customers through word-of-mouth — which is great. But you're missing everyone who searches Google first, and that's 80% of new customers today.

I'm Sandeep, a web developer from Hyderabad. I build fast, professional websites for local businesses that load under 1 second, work on mobile, and show up on Google.

Can I show you a free concept of what a {name} website could look like? No commitment at all.

Best,
{YOUR_NAME}
📞 {YOUR_PHONE}
🌐 {YOUR_PORTFOLIO}

(Reply "not interested" anytime and I won't message again.)"""

    else:
        issues_block = "\n".join(f"  • {i}" for i in top3) if top3 else "  • Speed and mobile experience could be improved"
        subject = f"Found a few issues on {name}'s website"
        body = f"""Hi {name},

I came across {name}'s website while looking for {category} in {city} and noticed a few things that might be costing you customers:

{issues_block}

I'm Sandeep, a web developer from Hyderabad. I build modern websites using Next.js that load in under 1 second and work perfectly on every device.

I'd love to show you a free concept of what an improved {name} site could look like — takes me 20 minutes and no commitment from you.

Worth a quick chat?

Best,
{YOUR_NAME}
📞 {YOUR_PHONE}
🌐 {YOUR_PORTFOLIO}

(Reply "not interested" anytime and I won't message again.)"""

    return subject, body


def _load_sent() -> set:
    seen = set()
    for f in [SENT_LOG, OPT_OUT_LOG]:
        if not os.path.exists(f): continue
        with open(f, "r", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                seen.add(row.get("email","").lower())
                seen.add(row.get("business_name","").lower())
    return seen


def _count_today() -> int:
    if not os.path.exists(SENT_LOG): return 0
    today = datetime.now().strftime("%Y-%m-%d")
    with open(SENT_LOG,"r",encoding="utf-8") as f:
        return sum(1 for r in csv.DictReader(f) if r.get("date","").startswith(today))


def _log_sent(lead: dict, email: str):
    exists = os.path.exists(SENT_LOG)
    with open(SENT_LOG,"a",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","business_name","email","city","category"])
        if not exists: w.writeheader()
        w.writerow({
            "date":          datetime.now().strftime("%Y-%m-%d %H:%M"),
            "business_name": lead.get("name",""),
            "email":         email,
            "city":          lead.get("city",""),
            "category":      lead.get("category",""),
        })


def _send_gmail(to: str, subject: str, body: str) -> bool:
    if not GMAIL_APP_PASSWORD:
        print("  [Sender] No GMAIL_APP_PASSWORD in .env — skipping")
        return False
    try:
        msg = MIMEMultipart()
        msg["From"]     = f"{YOUR_NAME} <{GMAIL_ADDRESS}>"
        msg["To"]       = to
        msg["Subject"]  = subject
        msg["Reply-To"] = GMAIL_ADDRESS
        msg.attach(MIMEText(body, "plain"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"  [Sender] Error: {e}")
        return False


def run_outreach(leads: list):
    sent_today = _count_today()
    if sent_today >= DAILY_LIMIT:
        print(f"  [Sender] Daily limit ({DAILY_LIMIT}) reached — resuming tomorrow")
        return

    already = _load_sent()
    queue = [
        l for l in leads
        if l.get("email","").strip()
        and l.get("priority") in ("HIGH","MEDIUM")
        and l.get("email","").lower() not in already
        and l.get("name","").lower() not in already
    ]

    print(f"  [Sender] {len(queue)} queued | {sent_today}/{DAILY_LIMIT} sent today")

    sent_count = 0
    for lead in queue:
        if _count_today() >= DAILY_LIMIT:
            print(f"  [Sender] Daily limit ({DAILY_LIMIT}) hit — done for today ✓")
            break

        email = lead["email"]
        subject, body = _build_email(lead)
        print(f"\n  📧 Sending to: {lead.get('name')} <{email}>")
        print(f"     Subject: {subject}")

        if _send_gmail(email, subject, body):
            _log_sent(lead, email)
            sent_count += 1
            print(f"     ✅ SENT ({_count_today()}/{DAILY_LIMIT} today)")
        else:
            print(f"     ❌ Failed — check GMAIL_APP_PASSWORD secret")

        # Random 2–4 min gap between sends — looks human to Gmail
        if lead != queue[-1]:
            wait = random.randint(120, 240)
            print(f"     ⏱  Waiting {wait//60}m {wait%60}s before next send ...")
            time.sleep(wait)

    print(f"\n  [Sender] Run complete — {sent_count} emails sent this run")
