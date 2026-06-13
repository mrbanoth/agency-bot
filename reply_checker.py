"""
reply_checker.py
Checks your Gmail inbox for replies to outreach emails.
When someone replies, it immediately emails YOU with:
  - Their message
  - A suggested reply template
  - Their lead details

You then reply from Gmail yourself — the bot never impersonates you.
"""

import sys, imaplib, email, smtplib, ssl, csv, os
from email.header import decode_header
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, YOUR_NAME, YOUR_PHONE, YOUR_PORTFOLIO

REPLIED_LOG = "replied_log.csv"


def _decode(val) -> str:
    if not val: return ""
    decoded, enc = decode_header(val)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(enc or "utf-8", errors="ignore")
    return decoded


def _get_body(msg) -> str:
    """Extract plain text body from email."""
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


def _log_replied(message_id: str, sender: str, subject: str):
    exists = os.path.exists(REPLIED_LOG)
    with open(REPLIED_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","message_id","sender","subject"])
        if not exists: w.writeheader()
        w.writerow({
            "date":       datetime.now().strftime("%Y-%m-%d %H:%M"),
            "message_id": message_id,
            "sender":     sender,
            "subject":    subject,
        })


def _notify_sandeep(sender_email: str, sender_name: str, subject: str, body: str):
    """Email Sandeep that someone replied, with suggested response."""
    if not GMAIL_APP_PASSWORD: return

    suggestion = f"""Hi {sender_name or 'there'},

Thank you for getting back to me!

I'd love to show you what we can do for your business. Would you be available for a quick 15-minute call this week?

I can walk you through:
- What your new website would look like
- How it will help you get more customers
- Timeline and pricing

Looking forward to connecting!

Best,
{YOUR_NAME}
📞 {YOUR_PHONE}
🌐 {YOUR_PORTFOLIO}"""

    html = f"""
<html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;padding:20px">
  <div style="background:#27ae60;color:#fff;padding:15px;border-radius:8px">
    <h2 style="margin:0">🎉 Someone Replied to Your Outreach!</h2>
  </div>
  <div style="margin:20px 0;padding:15px;background:#f8f9fa;border-radius:8px">
    <b>From:</b> {sender_name} &lt;{sender_email}&gt;<br>
    <b>Subject:</b> {subject}<br>
    <b>Time:</b> {datetime.now().strftime('%d %b %Y, %I:%M %p')}
  </div>
  <h3>Their Message:</h3>
  <div style="padding:15px;border-left:4px solid #27ae60;background:#fff;white-space:pre-wrap;font-size:14px">{body[:1500]}</div>
  <h3>📝 Suggested Reply (copy-paste this):</h3>
  <div style="padding:15px;border-left:4px solid #3498db;background:#eaf4fb;white-space:pre-wrap;font-size:14px">{suggestion}</div>
  <p style="color:#999;font-size:12px;margin-top:30px">
    ⚡ Reply to them directly from your Gmail — do NOT use the bot to reply.
    This is your chance to close the deal personally!
  </p>
</body></html>"""

    try:
        msg = __import__("email.mime.multipart", fromlist=["MIMEMultipart"]).MIMEMultipart("alternative")
        msg["Subject"] = f"🎉 {sender_name or sender_email} replied to your outreach!"
        msg["From"]    = GMAIL_ADDRESS
        msg["To"]      = GMAIL_ADDRESS
        msg.attach(__import__("email.mime.text", fromlist=["MIMEText"]).MIMEText(html, "html"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.send_message(msg)
        print(f"  [Reply] Notified you about reply from {sender_email}")
    except Exception as e:
        print(f"  [Reply] Notification error: {e}")


def check_replies():
    """Scan inbox for replies to outreach. Notify Sandeep for each new one."""
    if not GMAIL_APP_PASSWORD:
        print("  [Reply Checker] No GMAIL_APP_PASSWORD — skipping")
        return

    already_seen = _load_replied()
    new_replies  = 0

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        mail.select("inbox")

        # Search for unread emails that are replies (have Re: in subject)
        _, data = mail.search(None, 'UNSEEN SUBJECT "Re:"')
        ids = data[0].split()
        print(f"  [Reply Checker] {len(ids)} unread replies found")

        for eid in ids:
            _, msg_data = mail.fetch(eid, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            message_id  = msg.get("Message-ID", str(eid))
            sender_raw  = msg.get("From", "")
            subject     = _decode(msg.get("Subject",""))
            body        = _get_body(msg).strip()

            # Parse sender
            if "<" in sender_raw:
                sender_name  = sender_raw.split("<")[0].strip().strip('"')
                sender_email = sender_raw.split("<")[1].strip(">")
            else:
                sender_name  = ""
                sender_email = sender_raw.strip()

            # Skip our own emails and already processed ones
            if sender_email.lower() == GMAIL_ADDRESS.lower(): continue
            if message_id in already_seen: continue

            # Skip unsubscribe replies silently
            if any(w in body.lower() for w in ["not interested","unsubscribe","remove me","stop"]):
                print(f"  [Reply] {sender_email} opted out — skipping")
                _log_replied(message_id, sender_email, subject)
                continue

            # New interested reply — notify Sandeep
            _notify_sandeep(sender_email, sender_name, subject, body)
            _log_replied(message_id, sender_email, subject)
            new_replies += 1

        mail.logout()
        print(f"  [Reply Checker] {new_replies} new interested replies — check your email!")

    except Exception as e:
        print(f"  [Reply Checker] IMAP error: {e}")
        print("  Tip: Enable IMAP in Gmail → Settings → See all settings → Forwarding and POP/IMAP")
