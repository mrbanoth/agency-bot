"""
follow_up.py — Automated 5-day follow-up emails

Most sales happen on the 2nd or 3rd contact.
This sends ONE short follow-up to every lead that:
  - Got a cold email 5+ days ago
  - Has NOT replied
  - Has NOT already received a follow-up

Short, human, non-pushy. Different from the cold email.
"""

import sys, os, smtplib, ssl, time, random
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

import tracker
from config import (
    GMAIL_ADDRESS, GMAIL_APP_PASSWORD,
    YOUR_NAME, YOUR_PHONE, YOUR_PORTFOLIO,
    FOLLOW_UP_DAYS, SECOND_FOLLOWUP_DAYS,
)

FOLLOWUP_DAILY_CAP = 15   # keep well within Gmail limits


# ── Build the follow-up email ──────────────────────────────────

def _build_followup(email: str, data: dict) -> tuple:
    name     = data.get("business_name", "")
    first    = name.split()[0] if name else "there"
    has_site = bool(data.get("website", "").strip())
    category = data.get("category", "business")

    # Variant A — for businesses with no website
    if not has_site:
        subject = f"Re: {name} — still happy to help"
        body = f"""Hey {first},

Just following up on my previous email.

I know running a {category} keeps you busy, so I'll be quick — I'd love to put together a free website concept for {name}, just to show you what's possible.

No cost, no pressure, just a quick look. If you like it, great. If not, no hard feelings at all.

Worth 5 minutes?

Sandeep
{YOUR_PHONE}
{YOUR_PORTFOLIO}"""

    # Variant B — for businesses with a bad website
    else:
        subject = f"Re: {name}'s website — quick thought"
        body = f"""Hey {first},

Following up on my email from last week about your website.

I noticed {name} has a few things that could be improved to bring in more customers — nothing drastic, just some targeted fixes.

I'd love to share what I'd do specifically for you. Just 5 minutes of your time — reply here and I'll send it over.

Sandeep
{YOUR_PHONE}
{YOUR_PORTFOLIO}"""

    return subject, body


# ── Send via Gmail ─────────────────────────────────────────────

def _send(to: str, subject: str, body: str) -> bool:
    if not GMAIL_APP_PASSWORD:
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
        print(f"  [Follow-up] Send error: {e}")
        return False


# ── Main function ──────────────────────────────────────────────

def run_follow_ups():
    """Send follow-ups to cold leads that haven't replied in FOLLOW_UP_DAYS days."""
    if not GMAIL_APP_PASSWORD:
        print("  [Follow-up] No GMAIL_APP_PASSWORD — skipping")
        return

    all_convs = tracker.get_all()

    # Find leads ready for follow-up
    candidates = [
        (email, data)
        for email, data in all_convs.items()
        if data.get("stage") == "COLD_SENT"
        and not data.get("follow_up_sent", False)
        and tracker.days_since(data.get("cold_sent_date", "")) >= FOLLOW_UP_DAYS
    ]

    print(f"  [Follow-up] {len(candidates)} leads ready for follow-up (>{FOLLOW_UP_DAYS} days, no reply)")

    if not candidates:
        return

    sent = 0
    for email, data in candidates:
        if sent >= FOLLOWUP_DAILY_CAP:
            print(f"  [Follow-up] Daily cap ({FOLLOWUP_DAILY_CAP}) reached")
            break

        subject, body = _build_followup(email, data)
        name = data.get("business_name", email)

        print(f"\n  📩 Follow-up → {name} <{email}>")

        if _send(email, subject, body):
            tracker.update(
                email,
                follow_up_sent=True,
                stage="FOLLOW_UP_SENT",
                last_contact=datetime.now().strftime("%Y-%m-%d"),
            )
            sent += 1
            print(f"     ✅ Sent ({sent}/{FOLLOWUP_DAILY_CAP})")
        else:
            print(f"     ❌ Failed")

        # Small random gap — looks human
        if sent < len(candidates):
            wait = random.randint(60, 150)
            time.sleep(wait)

    print(f"\n  [Follow-up] Done — {sent} follow-ups sent this run")


def run_second_followups():
    """Send second follow-ups to leads remaining silent for SECOND_FOLLOWUP_DAYS days since cold email."""
    if not GMAIL_APP_PASSWORD:
        print("  [Second Follow-up] No GMAIL_APP_PASSWORD — skipping")
        return

    all_convs = tracker.get_all()

    candidates = [
        (email, data)
        for email, data in all_convs.items()
        if data.get("stage") == "FOLLOW_UP_SENT"
        and not data.get("second_followup_sent", False)
        and tracker.days_since(data.get("cold_sent_date", "")) >= SECOND_FOLLOWUP_DAYS
    ]

    print(f"  [Second Follow-up] {len(candidates)} leads ready for second follow-up (>={SECOND_FOLLOWUP_DAYS} days, no reply)")

    if not candidates:
        return

    sent = 0
    for email, data in candidates:
        if sent >= 10:   # Daily cap of 10
            print("  [Second Follow-up] Daily cap (10) reached")
            break

        name = data.get("business_name", "")
        first = name.split()[0] if name else "there"
        subject = f"Re: {name} — final try"
        body = f"""Hey {first},

Last email from me — I don't want to keep bothering you.

If you ever want to talk about your website, I'm here.

— Sandeep
{YOUR_PHONE}
{YOUR_PORTFOLIO}"""

        print(f"\n  📩 Second Follow-up → {name} <{email}>")
        if _send(email, subject, body):
            tracker.update(
                email,
                second_followup_sent=True,
                stage="SECOND_FOLLOWUP_SENT",
                last_contact=datetime.now().strftime("%Y-%m-%d"),
            )
            sent += 1
            print(f"     ✅ Sent ({sent}/10 today)")
        else:
            print(f"     ❌ Failed")

        if sent < len(candidates):
            time.sleep(random.randint(60, 150))

    print(f"\n  [Second Follow-up] Done — {sent} second follow-ups sent this run")
