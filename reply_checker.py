"""
reply_checker.py — AI-powered conversation handler

Full pipeline:
  1. Read Gmail inbox for replies to outreach emails
  2. Classify intent with Groq AI:
       INTERESTED  → wants to know more
       PRICING     → asking about cost
       QUESTION    → specific question about website/work
       CONFIRM     → ready to hire / wants a proposal
       NOT_INTERESTED → declining
       VAGUE       → unclear, send a friendly nudge
  3. Auto-reply in Sandeep's voice — sounds 100% human
  4. Track conversation stage per lead in conversations.json
  5. ONLY alert Sandeep when CONFIRM detected (hot lead ready to hire)
"""

import sys, imaplib, email, smtplib, ssl, csv, os, re, time
from email.header import decode_header
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

import tracker   # shared state manager — no circular imports
import telegram_notifier
import voice_caller
from config import (
    GMAIL_ADDRESS, GMAIL_APP_PASSWORD,
    YOUR_NAME, YOUR_PHONE, YOUR_PORTFOLIO, YOUR_EMAIL,
    GROQ_API_KEY, GROQ_MODEL,
)

REPLIED_LOG   = "replied_log.csv"
SENT_LOG      = "sent_log.csv"
MAX_EXCHANGES = 4   # max auto-replies per lead before handing off to Sandeep

def _get_lead_context(sender_email: str) -> dict:
    """Look up lead details from tracker (conversations.json) or sent_log.csv fallback."""
    data = tracker.get(sender_email)
    if data:
        return data
    # Fallback: check sent_log.csv for leads registered before tracker existed
    if os.path.exists(SENT_LOG):
        with open(SENT_LOG, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("email","").lower() == sender_email.lower().strip():
                    return {
                        "business_name": row.get("business_name",""),
                        "category":      row.get("category",""),
                        "city":          row.get("city",""),
                        "website":       "",
                        "phone":         "",
                        "stage":         "COLD_SENT",
                        "exchanges":     0,
                        "qualified":     False,
                    }
    return {}


# ── Email helpers ──────────────────────────────────────────────

def _decode_str(val) -> str:
    if not val: return ""
    decoded, enc = decode_header(val)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(enc or "utf-8", errors="ignore")
    return str(decoded)


def _get_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_payload(decode=True).decode("utf-8", errors="ignore")
                except Exception:
                    pass
    else:
        try:
            return msg.get_payload(decode=True).decode("utf-8", errors="ignore")
        except Exception:
            return ""
    return ""


def _load_replied() -> set:
    seen = set()
    if not os.path.exists(REPLIED_LOG): return seen
    with open(REPLIED_LOG, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seen.add(row.get("message_id",""))
    return seen


def _log_replied(message_id: str, sender: str, subject: str, intent: str):
    exists = os.path.exists(REPLIED_LOG)
    with open(REPLIED_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","message_id","sender","subject","intent"])
        if not exists: w.writeheader()
        w.writerow({
            "date":       datetime.now().strftime("%Y-%m-%d %H:%M"),
            "message_id": message_id,
            "sender":     sender,
            "subject":    subject,
            "intent":     intent,
        })


def _send_email(to: str, subject: str, body: str, reply_to_msg_id: str = None) -> bool:
    if not GMAIL_APP_PASSWORD:
        return False
    try:
        msg = MIMEMultipart()
        msg["From"]    = f"{YOUR_NAME} <{GMAIL_ADDRESS}>"
        msg["To"]      = to
        msg["Subject"] = subject
        if reply_to_msg_id:
            msg["In-Reply-To"] = reply_to_msg_id
            msg["References"]  = reply_to_msg_id
        msg.attach(MIMEText(body, "plain"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"  [AutoReply] Send error: {e}")
        return False


# ── Groq AI: classify + generate reply ────────────────────────

def _classify_intent(reply_text: str, business_name: str) -> str:
    """Classify reply intent using Groq. Falls back to rule-based."""
    if GROQ_API_KEY:
        try:
            import requests as req
            resp = req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [{
                        "role": "user",
                        "content": f"""You received this email reply from a business owner ({business_name}) after a web developer sent them a cold outreach email about building/improving their website.

Reply text:
\"\"\"{reply_text[:800]}\"\"\"

Classify as exactly ONE of these (reply with just the word):
INTERESTED   - positive response, wants to know more, open to discussion
PRICING      - asking specifically about cost, rates, pricing, packages
QUESTION     - asking specific technical questions (timeline, process, examples, portfolio)
CONFIRM      - clearly wants to proceed, requesting a proposal/quote, saying yes/let's do it
NOT_INTERESTED - declining, not interested, remove me, too busy
VAGUE        - too short or unclear to determine intent

Reply with only one word from the list above."""
                    }],
                    "max_tokens": 10,
                    "temperature": 0,
                },
                timeout=10,
            )
            result = resp.json()["choices"][0]["message"]["content"].strip().upper()
            if result in ("INTERESTED","PRICING","QUESTION","CONFIRM","NOT_INTERESTED","VAGUE"):
                return result
        except Exception as e:
            print(f"  [AI] Classification error: {e}")

    # Rule-based fallback
    text = reply_text.lower()
    if any(w in text for w in ["not interested","remove","unsubscribe","stop","no thanks","don't contact"]):
        return "NOT_INTERESTED"
    if any(w in text for w in ["yes","confirm","proceed","let's go","send proposal","hire","finalize","book","start","deal"]):
        return "CONFIRM"
    if any(w in text for w in ["price","cost","rate","charge","how much","budget","package","fee"]):
        return "PRICING"
    if any(w in text for w in ["portfolio","example","previous work","show me","timeline","how long","process","demo"]):
        return "QUESTION"
    if any(w in text for w in ["interested","sure","sounds good","tell me more","details","more info","okay"]):
        return "INTERESTED"
    return "VAGUE"


def _generate_reply(intent: str, lead_ctx: dict, their_reply: str, sender_name: str) -> str:
    """Generate a human-like reply using Groq. Falls back to templates."""
    name     = sender_name or lead_ctx.get("business_name","there")
    category = lead_ctx.get("category","business")
    city     = lead_ctx.get("city","your city")
    first    = name.split()[0] if name else "there"

    if GROQ_API_KEY:
        try:
            import requests as req
            resp = req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [{
                        "role": "user",
                        "content": f"""You are Sandeep Naik, a freelance web developer from Hyderabad, India.
Write a SHORT, friendly, professional email reply to a {category} business owner in {city}.

Their reply: "{their_reply[:400]}"
Intent type: {intent}
Their name (use first name only): {first}
Your portfolio: {YOUR_PORTFOLIO}
Your phone: {YOUR_PHONE}

Rules:
- Under 120 words
- Sound like a real person, NOT a corporate bot
- No bullet points — just conversational paragraphs
- No "I hope this email finds you well" or similar clichés
- For INTERESTED: mention portfolio link naturally, ask about a quick call
- For PRICING: give range ₹8,000–₹25,000 depending on requirements, say exact quote needs a quick chat
- For QUESTION: answer briefly, reference portfolio for examples, suggest a call
- For VAGUE: friendly, ask what they're looking to do
- End by suggesting a 10-minute call or asking what works for them
- Sign as: Sandeep (then new line) {YOUR_PHONE}

Write only the email body, nothing else."""
                    }],
                    "max_tokens": 200,
                    "temperature": 0.7,
                },
                timeout=15,
            )
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"  [AI] Reply generation error: {e}")

    # ── Template fallback ──
    if intent == "PRICING":
        return f"""Hey {first},

Thanks for asking! Pricing depends on what you need, but here's a rough idea:

Basic site (5 pages, mobile-friendly, fast loading): ₹8,000–₹12,000
Full site with contact forms, gallery, Google Maps, SEO: ₹15,000–₹22,000
Custom features or booking system: ₹25,000+

All one-time. No monthly fees. Includes 1 month of free support after launch.

Would love to give you an exact quote — takes just a 10-minute call. You can also see examples of my work at {YOUR_PORTFOLIO}.

What time works for a quick chat?

Sandeep
{YOUR_PHONE}"""

    elif intent == "QUESTION":
        return f"""Hey {first},

Great question! You can see my recent work at {YOUR_PORTFOLIO} — happy to walk you through specific examples relevant to your business.

Most projects take 7–14 days from start to launch. Process is simple: I understand your requirements, send you a design for approval, then build and launch.

Would a quick 10-minute call work to discuss what you're looking for? Just let me know a time that works.

Sandeep
{YOUR_PHONE}"""

    elif intent == "VAGUE":
        return f"""Hey {first},

Thanks for getting back!

I'd love to understand what you're looking for. Whether it's a brand new website or improving your existing one, I can help.

You can see some of my work at {YOUR_PORTFOLIO}. Can we jump on a quick 10-minute call this week? Makes it much easier to understand your requirements and give you a proper plan.

Sandeep
{YOUR_PHONE}"""

    else:  # INTERESTED (default)
        return f"""Hey {first},

Thanks for getting back — really glad you're open to this!

I've helped quite a few {category} businesses get a proper online presence that actually brings in customers. You can see some examples at {YOUR_PORTFOLIO}.

To give you a sense of what I'd build for {name}: fast loading, mobile-first, connected to Google Maps, with your services and contact info front and centre.

Pricing is usually in the ₹8,000–₹22,000 range depending on what you need. Would love to figure out the right fit for you on a quick 10-minute call — what does your week look like?

Sandeep
{YOUR_PHONE}"""


# ── Alert Sandeep: HOT LEAD CONFIRMED ─────────────────────────

def _alert_hot_lead(sender_email: str, sender_name: str, subject: str, body: str, lead_ctx: dict):
    """Send urgent alert to Sandeep when someone confirms they want to hire."""
    if not GMAIL_APP_PASSWORD: return

    biz    = lead_ctx.get("business_name","")
    cat    = lead_ctx.get("category","")
    city   = lead_ctx.get("city","")
    phone  = lead_ctx.get("phone","")
    web    = lead_ctx.get("website","")

    html = f"""
<html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;padding:20px">
  <div style="background:#e74c3c;color:#fff;padding:20px;border-radius:8px">
    <h1 style="margin:0">🚨 HOT LEAD — CONTACT THEM NOW</h1>
    <p style="margin:5px 0;opacity:0.9">Someone is ready to hire you. Call or reply within 1 hour.</p>
  </div>

  <div style="background:#fff3cd;border:2px solid #ffc107;padding:15px;border-radius:8px;margin:20px 0">
    <h2 style="margin:0 0 10px 0;color:#856404">Business Details</h2>
    <table style="width:100%;font-size:15px">
      <tr><td><b>Business:</b></td><td>{biz}</td></tr>
      <tr><td><b>Category:</b></td><td>{cat}</td></tr>
      <tr><td><b>City:</b></td><td>{city}</td></tr>
      <tr><td><b>Email:</b></td><td><a href="mailto:{sender_email}">{sender_email}</a></td></tr>
      <tr><td><b>Phone:</b></td><td>{phone or "— check their website"}</td></tr>
      <tr><td><b>Website:</b></td><td>{web or "No website"}</td></tr>
    </table>
  </div>

  <h3>Their Message:</h3>
  <div style="padding:15px;border-left:4px solid #e74c3c;background:#fff;white-space:pre-wrap;font-size:14px">{body[:1500]}</div>

  <div style="background:#d4edda;border:1px solid #c3e6cb;padding:15px;border-radius:8px;margin-top:20px">
    <h3 style="color:#155724;margin:0 0 10px 0">✅ What to do now:</h3>
    <p style="margin:5px 0;color:#155724">1. Call them at <b>{phone or sender_email}</b> within 1 hour</p>
    <p style="margin:5px 0;color:#155724">2. Confirm requirements and timeline</p>
    <p style="margin:5px 0;color:#155724">3. Send a proposal/invoice</p>
    <p style="margin:5px 0;color:#155724">4. Start building! 🚀</p>
  </div>

  <p style="color:#999;font-size:12px;margin-top:20px">
    The bot has already sent them a "I'll be in touch shortly" reply.<br>
    {datetime.now().strftime('%d %b %Y, %I:%M %p IST')}
  </p>
</body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 HOT LEAD — {biz or sender_name} wants to hire you! Call NOW"
        msg["From"]    = GMAIL_ADDRESS
        msg["To"]      = YOUR_EMAIL
        msg.attach(MIMEText(html, "html"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.send_message(msg)
        print(f"  🚨 HOT LEAD ALERT sent to {YOUR_EMAIL} for {biz or sender_name}!")
        
        # Trigger Telegram Alerts (Twilio call alerts disabled to avoid costs)
        issues = lead_ctx.get("issues", "")
        telegram_notifier.alert_hot_lead(biz or sender_name, city, phone, sender_email, web, issues)
        # voice_caller.call_sandeep(biz or sender_name, city, phone)
        
    except Exception as e:
        print(f"  [Alert] Error: {e}")


def _confirm_reply_to_lead(to: str, lead_ctx: dict, their_msg_id: str):
    """When someone confirms, send them a quick 'I'll be in touch' before Sandeep calls."""
    name  = lead_ctx.get("business_name","")
    first = name.split()[0] if name else "there"
    body  = f"""Hey {first},

Perfect — I'll get in touch with you shortly to discuss the details and put together a proposal for you.

Talk soon!

Sandeep
{YOUR_PHONE}
{YOUR_PORTFOLIO}"""
    _send_email(to, "Re: Your website", body, their_msg_id)


# ── Main function ──────────────────────────────────────────────

def check_replies():
    """Scan inbox, classify every reply, auto-respond, alert Sandeep only on hot leads."""
    if not GMAIL_APP_PASSWORD:
        print("  [Reply Checker] No GMAIL_APP_PASSWORD — skipping")
        return

    already_seen = _load_replied()
    new_replies  = 0
    auto_sent    = 0
    hot_leads    = 0

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        mail.select("inbox")

        # Look for all unread replies
        _, data = mail.search(None, 'UNSEEN SUBJECT "Re:"')
        ids = data[0].split()
        print(f"  [Reply Checker] {len(ids)} unread replies in inbox")

        for eid in ids:
            _, msg_data = mail.fetch(eid, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            message_id  = msg.get("Message-ID", str(eid))
            sender_raw  = msg.get("From", "")
            subject     = _decode_str(msg.get("Subject",""))
            body        = _get_body(msg).strip()

            # Parse sender
            if "<" in sender_raw:
                sender_name  = sender_raw.split("<")[0].strip().strip('"')
                sender_email = sender_raw.split("<")[1].strip(">").lower()
            else:
                sender_name  = ""
                sender_email = sender_raw.strip().lower()

            # Skip own emails and already handled ones
            if sender_email == GMAIL_ADDRESS.lower(): continue
            if message_id in already_seen: continue

            print(f"\n  📨 Reply from: {sender_name or sender_email}")

            # Get lead context
            lead_ctx = _get_lead_context(sender_email)
            biz_name = lead_ctx.get("business_name","") or sender_name

            # Check exchange limit (don't auto-reply forever)
            exchanges = lead_ctx.get("exchanges", 0)

            # ── Classify intent ──
            intent = _classify_intent(body, biz_name)
            print(f"     Intent: {intent}")

            # ── Handle each intent ──
            if intent == "NOT_INTERESTED":
                print(f"     → Opted out — marked and skipped")
                tracker.update(sender_email, stage="OPTED_OUT", business_name=biz_name)
                _log_replied(message_id, sender_email, subject, intent)
                continue

            elif intent == "CONFIRM":
                # 🚨 HOT LEAD — alert Sandeep immediately
                _alert_hot_lead(sender_email, sender_name or biz_name, subject, body, lead_ctx)
                _confirm_reply_to_lead(sender_email, lead_ctx, message_id)
                tracker.update(sender_email, stage="QUALIFIED", qualified=True, business_name=biz_name)
                hot_leads += 1

            elif exchanges >= MAX_EXCHANGES:
                # Had enough back-and-forth — hand off to Sandeep
                _alert_hot_lead(sender_email, sender_name or biz_name, subject, body, lead_ctx)
                print(f"     → {MAX_EXCHANGES} exchanges done — alerted you to take over")
                tracker.update(sender_email, stage="HANDOFF")
                hot_leads += 1

            else:
                # Auto-reply in Sandeep's voice
                reply_body = _generate_reply(intent, lead_ctx, body, sender_name or biz_name)

                # Re: subject (keep thread)
                reply_subject = subject if subject.startswith("Re:") else f"Re: {subject}"

                if _send_email(sender_email, reply_subject, reply_body, message_id):
                    auto_sent += 1
                    print(f"     ✅ Auto-replied ({intent})")
                    tracker.update(
                        sender_email,
                        stage="REPLIED",
                        exchanges=exchanges + 1,
                        last_contact=datetime.now().strftime("%Y-%m-%d"),
                        business_name=biz_name,
                    )
                else:
                    print(f"     ❌ Auto-reply failed")

                time.sleep(2)

            new_replies += 1
            _log_replied(message_id, sender_email, subject, intent)
        mail.logout()

        print(f"\n  [Reply Checker] Done:")
        print(f"     Replies processed : {new_replies}")
        print(f"     Auto-replies sent : {auto_sent}")
        print(f"     🔥 Hot leads       : {hot_leads} — check {YOUR_EMAIL}!")

    except Exception as e:
        print(f"  [Reply Checker] IMAP error: {e}")
        print("  Tip: Gmail → Settings → See all settings → Forwarding/POP/IMAP → Enable IMAP")
