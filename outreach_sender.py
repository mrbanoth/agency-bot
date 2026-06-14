"""
outreach_sender.py — Automated cold email sender

Features:
  - 3 rotating email templates (A/B/C) — avoids spam filters
  - Max 20 emails/day — keeps Gmail account safe
  - Random 2–4 min gaps between sends — looks human
  - Never emails the same business twice (tracks in sent_log.csv)
  - Registers every sent email in conversations.json via tracker.py
"""

import sys, csv, os, time, smtplib, ssl, random, hashlib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

import tracker
from config import (
    GMAIL_ADDRESS, GMAIL_APP_PASSWORD,
    YOUR_NAME, YOUR_PHONE, YOUR_PORTFOLIO,
)

SENT_LOG    = "sent_log.csv"
DAILY_LIMIT = 20


# ── 3 Email template variants ──────────────────────────────────
# Rotated per lead based on business name hash — looks different
# to spam filters, increases deliverability and reply rates.

def _variant(lead: dict) -> str:
    """Pick A, B, or C consistently for this business."""
    h = int(hashlib.md5(lead.get("name","x").encode()).hexdigest(), 16)
    return ["A","B","C"][h % 3]


def _build_email(lead: dict) -> tuple:
    name     = lead.get("name", "Team")
    first    = name.split()[0] if name else name
    issues   = [i.strip() for i in lead.get("website_issues","").split("|") if i.strip()]
    has_site = bool(lead.get("website","").strip())
    category = lead.get("category", "business")
    city     = lead.get("city", "your city")
    top_issue = issues[0] if issues else "it's not optimised for mobile or Google"
    variant  = _variant(lead)

    # ── No website at all ──────────────────────────────────────
    if not has_site:
        if variant == "A":
            subject = f"Quick question about {name}"
            body = f"""Hi {first},

I was looking up {category} businesses in {city} and noticed {name} doesn't have a website yet.

Today, 8 out of 10 customers search Google before choosing a business. Without a website, you're invisible to almost all of them.

I'm Sandeep, a web developer from Hyderabad. I build clean, fast websites for local businesses that load in under 1 second, look great on phones, and actually show up on Google.

Can I put together a free concept for {name}? No commitment — just to show you what's possible.

Best,
Sandeep
{YOUR_PHONE}
{YOUR_PORTFOLIO}

(Reply "not interested" and I won't message again.)"""

        elif variant == "B":
            subject = f"{name} — I couldn't find you online"
            body = f"""Hi {first},

I searched for {name} online while researching {category} businesses in {city} — I couldn't find a website for you.

That means customers who search Google for your services are going straight to your competitors instead.

I specialise in building websites for small local businesses — fast, mobile-friendly, and Google-ready. Most of my clients start getting more calls within the first month.

I'd love to show you a free mock-up of what a {name} website could look like. Would that be useful?

Best,
Sandeep
{YOUR_PHONE}
{YOUR_PORTFOLIO}

(Reply "not interested" anytime and I won't contact again.)"""

        else:  # C
            subject = f"Free website concept for {name}?"
            body = f"""Hi {first},

I build websites for {category} businesses in India, and I noticed {name} doesn't have one yet.

I'd like to offer you something for free — a proper website concept designed specifically for {name}, showing what your homepage could look like, what pages you'd have, and how you'd appear on Google.

No obligation. Just a gift, because I'm confident you'll like what you see.

Interested?

Sandeep
{YOUR_PHONE}
{YOUR_PORTFOLIO}

(Reply "stop" to opt out.)"""

    # ── Has a website with issues ──────────────────────────────
    else:
        issues_block = "\n".join(f"• {i}" for i in issues[:3]) if issues else "• Mobile experience and loading speed could be improved"

        if variant == "A":
            subject = f"Found a few issues on {name}'s website"
            body = f"""Hi {first},

I came across {name}'s website while looking for {category} in {city} and ran a quick audit. Found a few things that might be costing you customers:

{issues_block}

I'm Sandeep, a web developer from Hyderabad. I build modern websites that fix exactly these kinds of issues — fast, mobile-first, and designed to convert visitors into customers.

I'd love to show you a free improvement concept for {name}. Takes me 20 minutes and no commitment from you at all.

Worth a look?

Sandeep
{YOUR_PHONE}
{YOUR_PORTFOLIO}

(Reply "not interested" anytime.)"""

        elif variant == "B":
            subject = f"Your website is losing you customers, {first}"
            body = f"""Hi {first},

I checked {name}'s website today and noticed something important:

{issues_block}

These are the exact things that make potential customers leave your site and go to a competitor. The good news — they're all fixable.

I'm Sandeep, a web developer from Hyderabad. I specialise in rebuilding local business websites to fix these issues and bring in more customers.

Can I send you a quick concept of what an improved {name} site could look like? Free, no strings attached.

Sandeep
{YOUR_PHONE}
{YOUR_PORTFOLIO}

(Reply "stop" to opt out.)"""

        else:  # C
            subject = f"Quick note about {name}'s website"
            body = f"""Hi {first},

While looking for {category} in {city}, I found {name}'s website. I noticed: {top_issue.lower()}.

That's one of the top reasons customers leave a site without getting in touch — and it's an easy fix.

I build websites for local businesses in India — clean, fast, mobile-friendly. I'd love to put together a free redesign concept specifically for {name}.

Would you be open to taking a look?

Sandeep
{YOUR_PHONE}
{YOUR_PORTFOLIO}

(Reply "not interested" to opt out.)"""

    return subject, body


# ── Tracking ───────────────────────────────────────────────────

def _load_sent() -> set:
    seen = set()
    if not os.path.exists(SENT_LOG): return seen
    with open(SENT_LOG, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seen.add(row.get("email","").lower())
            seen.add(row.get("business_name","").lower())
    return seen


def _count_today() -> int:
    if not os.path.exists(SENT_LOG): return 0
    today = datetime.now().strftime("%Y-%m-%d")
    with open(SENT_LOG, "r", encoding="utf-8") as f:
        return sum(1 for r in csv.DictReader(f) if r.get("date","").startswith(today))


def _log_sent(lead: dict, email: str):
    exists = os.path.exists(SENT_LOG)
    with open(SENT_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","business_name","email","city","category","variant"])
        if not exists: w.writeheader()
        w.writerow({
            "date":          datetime.now().strftime("%Y-%m-%d %H:%M"),
            "business_name": lead.get("name",""),
            "email":         email,
            "city":          lead.get("city",""),
            "category":      lead.get("category",""),
            "variant":       _variant(lead),
        })


# ── Gmail send ─────────────────────────────────────────────────

def _send_gmail(to: str, subject: str, body: str) -> bool:
    if not GMAIL_APP_PASSWORD:
        print("  [Sender] No GMAIL_APP_PASSWORD — skipping. Add it to GitHub Secrets.")
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


# ── Main function ──────────────────────────────────────────────

def run_outreach(leads: list):
    """Send cold emails to new hot/medium leads. Max 20/day."""
    sent_today = _count_today()
    if sent_today >= DAILY_LIMIT:
        print(f"  [Sender] Daily limit ({DAILY_LIMIT}) already reached — resuming tomorrow")
        return

    already = _load_sent()
    queue = [
        l for l in leads
        if l.get("email","").strip()
        and l.get("priority") in ("HIGH","MEDIUM")
        and l.get("email","").lower() not in already
        and l.get("name","").lower() not in already
    ]

    print(f"  [Sender] {len(queue)} in queue | {sent_today}/{DAILY_LIMIT} sent today")

    sent_count = 0
    for lead in queue:
        if _count_today() >= DAILY_LIMIT:
            print(f"  [Sender] Daily limit hit — done ✓")
            break

        email   = lead["email"]
        subject, body = _build_email(lead)
        var     = _variant(lead)

        print(f"\n  📧 [{var}] → {lead.get('name')} <{email}>")
        print(f"     {subject}")

        if _send_gmail(email, subject, body):
            _log_sent(lead, email)
            tracker.register(lead, email)   # track in conversations.json
            sent_count += 1
            print(f"     ✅ SENT ({_count_today()}/{DAILY_LIMIT} today)")
        else:
            print(f"     ❌ Failed")

        # Random 2–4 min gap — mimics human sending pattern
        if lead != queue[-1] and _count_today() < DAILY_LIMIT:
            wait = random.randint(120, 240)
            print(f"     ⏱  Waiting {wait//60}m {wait%60}s ...")
            time.sleep(wait)

    print(f"\n  [Sender] Run complete — {sent_count} emails sent this run")
