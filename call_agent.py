"""
call_agent.py — AI Phone Call Agent via Bland.ai
-------------------------------------------------
Automatically calls businesses, introduces Sandeep's services,
handles objections, and books a callback if they're interested.

Cost: ~₹4 per 30-second call (Bland.ai pricing)
To activate: Add BLAND_API_KEY to GitHub Secrets
Sign up:  app.bland.ai (no credit card for first 20 free test calls)

The bot calls using a natural voice and this exact script:
  → Introduces as calling on behalf of Sandeep
  → Mentions the specific website issue found
  → Offers a free concept demo
  → If interested → books a callback / asks for WhatsApp
  → If busy → offers to call back at a better time
  → If not interested → politely ends

NOTE: If BLAND_API_KEY is not set, this module does nothing.
      Everything else (email + WhatsApp) still runs normally.
"""

import os, csv, time, requests
from datetime import datetime

from config import (
    BLAND_API_KEY,
    YOUR_NAME, YOUR_PHONE, YOUR_PORTFOLIO,
)

CALL_LOG      = "call_log.csv"
DAILY_CALL_CAP = 10   # start with 10/day, increase once you see results


# ── AI call script (Bland.ai uses this as conversation guide) ──

def _build_call_script(lead: dict) -> str:
    name     = lead.get("name","this business")
    category = lead.get("category","business")
    city     = lead.get("city","your city")
    has_site = bool(lead.get("website","").strip())
    issues   = [i.strip() for i in lead.get("website_issues","").split("|") if i.strip()]
    issue    = issues[0] if issues else "it's not optimized for mobile"

    if not has_site:
        problem = f"{name} doesn't have a website yet, so they're missing customers who search online"
        offer   = "build them a professional website from scratch"
    else:
        problem = f"{name}'s website has an issue — {issue} — which could be costing them customers"
        offer   = "fix these issues and modernize their website"

    return f"""You are calling on behalf of Sandeep Naik, a web developer from Hyderabad, India.
Your goal: have a friendly 60-second conversation to see if {name} is interested in improving their online presence.

Introduction:
"Hi, is this {name}? Great — my name is calling on behalf of Sandeep, a web developer based in Hyderabad.
I'll be quick — I noticed that {problem}.
Sandeep specializes in helping {category} businesses get more customers through their website, and he'd love to show you a free concept — no cost, no commitment.
Would that be of interest to you?"

If YES / Interested:
"Wonderful! Sandeep will personally reach out to you on WhatsApp or email to show you what he has in mind.
Is WhatsApp okay? And is this the best number to reach you?
Great — you'll hear from him within 24 hours. Thanks so much and have a great day!"
[THEN: mark lead as INTERESTED in your response]

If BUSY / Call Back:
"Of course, I completely understand. When would be a better time to reach you — morning or afternoon?
Perfect — we'll make sure Sandeep reaches out then. Thanks and sorry for the interruption!"
[THEN: note preferred callback time in your response]

If NOT INTERESTED:
"No problem at all — I completely understand. Sorry for the interruption and have a wonderful day!"
[THEN: mark lead as NOT_INTERESTED in your response]

Keep the conversation natural, friendly, and under 60 seconds.
Speak clearly and at a moderate pace.
Do NOT be pushy — one polite ask, then accept their answer.
Portfolio to mention if asked: {YOUR_PORTFOLIO}
Sandeep's phone: {YOUR_PHONE}"""


# ── Helpers ────────────────────────────────────────────────────

def _format_phone(raw: str) -> str:
    digits = "".join(filter(str.isdigit, raw or ""))
    if digits.startswith("91") and len(digits) == 12:
        return "+" + digits
    if len(digits) == 10 and digits[0] in "6789":
        return "+91" + digits
    return ""


def _already_called(phone: str) -> bool:
    if not os.path.exists(CALL_LOG): return False
    with open(CALL_LOG, "r", encoding="utf-8") as f:
        return any(row.get("phone","") == phone for row in csv.DictReader(f))


def _log_call(phone: str, name: str, status: str):
    exists = os.path.exists(CALL_LOG)
    with open(CALL_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","phone","name","status"])
        if not exists: w.writeheader()
        w.writerow({
            "date":   datetime.now().strftime("%Y-%m-%d %H:%M"),
            "phone":  phone,
            "name":   name,
            "status": status,
        })


# ── Make the call via Bland.ai ─────────────────────────────────

def _make_call(to_phone: str, lead: dict) -> bool:
    script = _build_call_script(lead)
    try:
        resp = requests.post(
            "https://api.bland.ai/v1/calls",
            headers={
                "authorization": BLAND_API_KEY,
                "Content-Type":  "application/json",
            },
            json={
                "phone_number":   to_phone,
                "task":           script,
                "voice":          "nat",          # Indian-accent voice
                "language":       "en-IN",        # Indian English
                "max_duration":   2,              # max 2 minutes per call
                "record":         False,
                "amd":            True,           # skip answering machines
                "wait_for_greeting": True,
                "model":          "base",
                "interruption_threshold": 150,
                "metadata": {
                    "business": lead.get("name",""),
                    "city":     lead.get("city",""),
                    "category": lead.get("category",""),
                },
            },
            timeout=15,
        )
        if resp.status_code == 200:
            call_id = resp.json().get("call_id","")
            print(f"      Call initiated (ID: {call_id})")
            return True
        else:
            err = resp.json().get("message","unknown error")
            print(f"      Bland.ai error: {err}")
            return False
    except Exception as e:
        print(f"      Call error: {e}")
        return False


# ── Main function ──────────────────────────────────────────────

def run_call_outreach(leads: list):
    """Call HOT leads that have phone numbers. Only runs if BLAND_API_KEY is set."""
    if not BLAND_API_KEY:
        print("  [Calls] Skipped — add BLAND_API_KEY to GitHub Secrets to enable AI calls")
        print("          Sign up free: app.bland.ai (first 20 calls free)")
        return

    print(f"  [Calls] Starting AI call outreach ...")
    called = 0

    # Only call HIGH priority leads (best ROI)
    hot_leads = [l for l in leads if l.get("priority") == "HIGH" and l.get("phone","").strip()]

    for lead in hot_leads:
        if called >= DAILY_CALL_CAP:
            print(f"  [Calls] Daily cap ({DAILY_CALL_CAP}) reached")
            break

        phone = _format_phone(lead.get("phone",""))
        if not phone:
            continue
        if _already_called(phone):
            continue

        print(f"\n  📞 Calling: {lead.get('name')} ({phone})")
        if _make_call(phone, lead):
            _log_call(phone, lead.get("name",""), "INITIATED")
            called += 1
            print(f"     ✅ Call placed ({called}/{DAILY_CALL_CAP} today)")
        else:
            print(f"     ❌ Call failed")

        time.sleep(30)   # Bland.ai recommends 30s between calls

    print(f"\n  [Calls] Done — {called} calls placed this run")
