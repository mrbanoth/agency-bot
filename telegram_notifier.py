import sys
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def escape_html(text: str) -> str:
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def send_message(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  [Telegram] Warning: Bot token or chat ID is empty. Skipping.")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
        if resp.status_code == 200:
            return True
        else:
            print(f"  [Telegram] API error: {resp.text}")
            return False
    except Exception as e:
        print(f"  [Telegram] Send error: {e}")
        return False

def alert_hot_lead(business_name, city, phone, email, website, issues):
    text = (
        f"🚨 <b>HOT LEAD CONFIRMED</b> 🚨\n\n"
        f"<b>Business:</b> {escape_html(business_name)}\n"
        f"<b>City:</b> {escape_html(city)}\n"
        f"<b>Phone:</b> {escape_html(phone) or '—'}\n"
        f"<b>Email:</b> {escape_html(email) or '—'}\n"
        f"<b>Website:</b> {escape_html(website) or '—'}\n"
        f"<b>Issues:</b> {escape_html(issues) or '—'}\n\n"
        f"📞 Please contact them immediately!"
    )
    return send_message(text)

def send_daily_digest(city, hot, medium, emails_sent, calls_made):
    text = (
        f"📊 <b>DAILY DIGEST SUMMARY</b> 📊\n\n"
        f"<b>City Scraped:</b> {escape_html(city)}\n"
        f"<b>🔥 HOT Leads:</b> {hot}\n"
        f"<b>⚡ MEDIUM Leads:</b> {medium}\n"
        f"<b>📧 Emails Sent:</b> {emails_sent}\n"
        f"<b>📞 Voice Calls Made:</b> {calls_made}\n"
    )
    return send_message(text)
