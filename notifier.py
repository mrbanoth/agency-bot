"""
notifier.py
Sends YOU an email digest of hot leads found each run.
Uses Gmail SMTP — 100% free, no third-party service.
"""

import sys, smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, YOUR_EMAIL, YOUR_NAME, CITY


def _build_html(leads: list, run_time: str) -> str:
    high  = [l for l in leads if l.get("priority") == "HIGH"]
    med   = [l for l in leads if l.get("priority") == "MEDIUM"]

    def rows(lst):
        out = ""
        for l in lst:
            pitch = l.get("pitch", "").replace("\n", "<br>")
            out += f"""
            <tr>
              <td style="padding:10px;border-bottom:1px solid #eee">
                <b>{l.get('name','')}</b><br>
                <small style="color:#666">{l.get('category','')} · {l.get('city','')}</small>
              </td>
              <td style="padding:10px;border-bottom:1px solid #eee">
                {l.get('phone') or '<i style="color:#999">No phone</i>'}
              </td>
              <td style="padding:10px;border-bottom:1px solid #eee">
                {l.get('website') or '<i style="color:#999">No website</i>'}
              </td>
              <td style="padding:10px;border-bottom:1px solid #eee;font-size:12px">
                {l.get('website_issues','').replace('|','<br>')}
              </td>
              <td style="padding:10px;border-bottom:1px solid #eee;font-size:12px;color:#333">
                {pitch}
              </td>
            </tr>"""
        return out

    def table(lst, color, label):
        if not lst: return ""
        return f"""
        <h3 style="color:{color};margin-top:30px">{label} ({len(lst)} leads)</h3>
        <table style="width:100%;border-collapse:collapse;font-family:Arial,sans-serif;font-size:13px">
          <thead>
            <tr style="background:{color};color:#fff">
              <th style="padding:10px;text-align:left">Business</th>
              <th style="padding:10px;text-align:left">Phone</th>
              <th style="padding:10px;text-align:left">Website</th>
              <th style="padding:10px;text-align:left">Issues</th>
              <th style="padding:10px;text-align:left">Your Pitch</th>
            </tr>
          </thead>
          <tbody>{rows(lst)}</tbody>
        </table>"""

    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:1100px;margin:auto;padding:20px">
      <div style="background:#1a1a2e;color:#fff;padding:20px;border-radius:8px">
        <h2 style="margin:0">Agency Bot — Lead Digest</h2>
        <p style="margin:5px 0;color:#aaa">{run_time} · City: {CITY}</p>
      </div>
      <div style="background:#f8f9fa;padding:15px;border-radius:8px;margin:15px 0">
        <b>Summary:</b> &nbsp;
        🔥 <b style="color:#e74c3c">{len(high)} HIGH</b> &nbsp;|&nbsp;
        ⚡ <b style="color:#f39c12">{len(med)} MEDIUM</b> &nbsp;|&nbsp;
        📋 <b>{len(leads)} total</b>
      </div>
      {table(high, '#e74c3c', '🔥 HIGH PRIORITY — Pitch These First')}
      {table(med,  '#f39c12', '⚡ MEDIUM PRIORITY')}
      <hr style="margin-top:40px">
      <p style="color:#999;font-size:12px">
        Sent automatically by your Agency Bot · {YOUR_NAME}
      </p>
    </body></html>"""


def send_lead_digest(leads: list):
    """Email yourself a formatted digest of today's hot leads."""
    if not GMAIL_APP_PASSWORD:
        print("  [Notifier] No GMAIL_APP_PASSWORD set — skipping email. Add it to .env")
        return

    hot = [l for l in leads if l.get("priority") in ("HIGH", "MEDIUM")]
    if not hot:
        print("  [Notifier] No hot leads to email.")
        return

    run_time = datetime.now().strftime("%d %b %Y, %I:%M %p")
    high_count = len([l for l in hot if l.get("priority") == "HIGH"])

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔥 {high_count} Hot Leads Found — {CITY} ({run_time})"
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = YOUR_EMAIL

    html = _build_html(hot, run_time)
    msg.attach(MIMEText(html, "html"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print(f"  [Notifier] Email sent to {YOUR_EMAIL} — {len(hot)} leads")
    except Exception as e:
        print(f"  [Notifier] Email failed: {e}")


def send_error_alert(error_msg: str):
    """Email yourself if the bot crashes."""
    if not GMAIL_APP_PASSWORD:
        return
    try:
        msg = MIMEMultipart()
        msg["Subject"] = "⚠️ Agency Bot Error"
        msg["From"]    = GMAIL_ADDRESS
        msg["To"]      = YOUR_EMAIL
        msg.attach(MIMEText(f"<pre>{error_msg}</pre>", "html"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
    except Exception:
        pass
