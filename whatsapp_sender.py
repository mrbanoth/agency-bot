"""
whatsapp_sender.py — Free WhatsApp outreach via Meta Cloud API
--------------------------------------------------------------
FREE: 1,000 conversations/month (no credit card ever)

One-time setup (10 minutes):
  1. Go to developers.facebook.com → Log in with Facebook
  2. Click "Create App" → Choose "Business" → Give it a name
  3. In the app dashboard → Add Product → WhatsApp → Set Up
  4. Go to WhatsApp → API Setup
  5. Under "Step 1", copy the "Temporary access token"
     → Add as GitHub Secret: WHATSAPP_TOKEN
  6. Under "Step 2", copy the Phone Number ID
     → Add as GitHub Secret: WHATSAPP_PHONE_ID
  7. For production (beyond sandbox): add your own WhatsApp number
     under "Step 5" → Phone Numbers → Add phone number

Why WhatsApp > Cold calls in India:
  - 95%+ of Indian business owners check WhatsApp daily
  - They can reply when convenient (not during busy hours)
  - Higher open rate than email (98% vs 20%)
  - Completely free via Meta API
"""

import os, csv, time, requests
from datetime import datetime

from config import (
    WHATSAPP_TOKEN, WHATSAPP_PHONE_ID,
    YOUR_NAME, YOUR_PHONE, YOUR_PORTFOLIO,
)

WA_LOG        = "whatsapp_log.csv"
DAILY_WA_CAP  = 40   # Meta allows much higher but 40/day keeps it safe


# ── Helpers ────────────────────────────────────────────────────

def _format_phone(raw: str) -> str:
    """Normalize Indian phone to WhatsApp format: 91XXXXXXXXXX"""
    digits = "".join(filter(str.isdigit, raw or ""))
    if digits.startswith("91") and len(digits) == 12:
        return digits
    if len(digits) == 10 and digits[0] in "6789":
        return "91" + digits
    return ""   # invalid


def _already_sent(phone: str) -> bool:
    if not os.path.exists(WA_LOG): return False
    with open(WA_LOG, "r", encoding="utf-8") as f:
        return any(row.get("phone","") == phone for row in csv.DictReader(f))


def _log_sent(phone: str, name: str):
    exists = os.path.exists(WA_LOG)
    with open(WA_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","phone","name"])
        if not exists: w.writeheader()
        w.writerow({"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "phone": phone, "name": name})


# ── Message builder ────────────────────────────────────────────

def _build_message(lead: dict) -> str:
    name     = lead.get("name", "")
    category = lead.get("category", "business")
    city     = lead.get("city", "")
    has_site = bool(lead.get("website", "").strip())
    issues   = [i.strip() for i in lead.get("website_issues","").split("|") if i.strip()]
    top_issue = issues[0] if issues else "slow on mobile"

    if not has_site:
        return f"""Hi, I'm Sandeep — web developer based in Hyderabad.

I found *{name}* on Google Maps while looking for {category} in {city}, but couldn't find a website for you.

Today, 80% of customers search online before visiting a business. Without a website, you're invisible to all of them.

I build fast, professional websites for local businesses starting at ₹8,000. Would love to show you a free concept — no commitment.

👉 See my work: {YOUR_PORTFOLIO}
📞 {YOUR_PHONE}

Just reply here if you're interested. (Reply STOP to opt out.)"""

    else:
        return f"""Hi, I'm Sandeep — web developer based in Hyderabad.

I came across *{name}* while looking for {category} in {city} and checked your website. I noticed it has an issue: *{top_issue}* — this could be costing you customers.

I build modern, fast websites using Next.js that load in under 1 second and work perfectly on every device.

I'd love to show you a free redesign concept for {name} — takes me 20 minutes, no strings attached.

👉 See my work: {YOUR_PORTFOLIO}
📞 {YOUR_PHONE}

Interested? Just reply here. (Reply STOP to opt out.)"""


# ── Send via Meta API ──────────────────────────────────────────

def _send_whatsapp(to_phone: str, message: str) -> bool:
    try:
        resp = requests.post(
            f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_ID}/messages",
            headers={
                "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                "Content-Type":  "application/json",
            },
            json={
                "messaging_product": "whatsapp",
                "to":   to_phone,
                "type": "text",
                "text": {"body": message, "preview_url": False},
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return True
        else:
            err = resp.json().get("error",{}).get("message","unknown")
            print(f"      WA API error: {err}")
            return False
    except Exception as e:
        print(f"      WA send error: {e}")
        return False


# ── Main function ──────────────────────────────────────────────

def run_whatsapp_outreach(leads: list):
    """Send WhatsApp messages to leads that have phone numbers."""
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        print("  [WhatsApp] Skipped — add WHATSAPP_TOKEN + WHATSAPP_PHONE_ID to GitHub Secrets")
        print("             Setup guide: developers.facebook.com (free, 10 min)")
        return

    sent = 0
    for lead in leads:
        if sent >= DAILY_WA_CAP:
            print(f"  [WhatsApp] Daily cap ({DAILY_WA_CAP}) reached")
            break

        if lead.get("priority") not in ("HIGH","MEDIUM"):
            continue

        raw_phone = lead.get("phone","")
        phone     = _format_phone(raw_phone)
        if not phone:
            continue   # no valid phone number

        if _already_sent(phone):
            continue   # already messaged them

        message = _build_message(lead)

        print(f"\n  📱 WhatsApp → {lead.get('name')} ({raw_phone})")
        if _send_whatsapp(phone, message):
            _log_sent(phone, lead.get("name",""))
            sent += 1
            print(f"     ✅ Sent ({sent}/{DAILY_WA_CAP} today)")
        else:
            print(f"     ❌ Failed")

        time.sleep(1.5)   # gentle rate limiting

    print(f"\n  [WhatsApp] Done — {sent} messages sent this run")
