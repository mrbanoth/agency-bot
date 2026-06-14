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

def alert_hot_lead(business_name, city, phone, email, website, issues, reply_body=""):
    trimmed_body = escape_html(reply_body[:1000]) if reply_body else ""
    body_section = f"\n💬 <b>Client Message:</b>\n<i>{trimmed_body}</i>\n" if trimmed_body else ""

    text = (
        f"🚨 <b>HOT LEAD CONFIRMED</b> 🚨\n\n"
        f"<b>Business:</b> {escape_html(business_name)}\n"
        f"<b>City:</b> {escape_html(city)}\n"
        f"<b>Phone:</b> {escape_html(phone) or '—'}\n"
        f"<b>Email:</b> {escape_html(email) or '—'}\n"
        f"<b>Website:</b> {escape_html(website) or '—'}\n"
        f"<b>Issues:</b> {escape_html(issues) or '—'}\n"
        f"{body_section}\n"
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

def handle_commands():
    """Fetch updates from Telegram, process any commands from Sandeep, and reply."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    import os, json, csv

    state_file = "telegram_state.json"
    last_id = 0
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                last_id = json.load(f).get("last_processed_update_id", 0)
        except Exception:
            pass

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        params = {"offset": last_id + 1, "timeout": 2}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return

        updates = resp.json().get("result", [])
        if not updates:
            return

        print(f"  [Telegram Commands] Found {len(updates)} new updates.")

        new_last_id = last_id
        for update in updates:
            new_last_id = max(new_last_id, update.get("update_id", 0))

            message = update.get("message")
            if not message:
                continue

            chat = message.get("chat", {})
            # Only handle commands from Sandeep
            if str(chat.get("id")) != str(TELEGRAM_CHAT_ID):
                continue

            text = message.get("text", "").strip()
            if not text.startswith("/"):
                continue

            cmd = text.split()[0].lower()
            print(f"  [Telegram Commands] Processing: {cmd}")

            if cmd == "/help":
                reply = (
                    "🤖 <b>Agency Bot Commands:</b>\n\n"
                    "<b>/status</b> — Get overall bot stats\n"
                    "<b>/leads</b> — List top 5 recent hot leads\n"
                    "<b>/replies</b> — Show recent client email replies\n"
                    "<b>/help</b> — Show this help message"
                )
                send_message(reply)

            elif cmd == "/status":
                # Count total leads
                total_leads = 0
                high_leads = 0
                medium_leads = 0
                if os.path.exists("leads.csv"):
                    try:
                        with open("leads.csv", "r", encoding="utf-8") as f:
                            rdr = csv.DictReader(f)
                            for row in rdr:
                                total_leads += 1
                                p = row.get("priority", "").upper()
                                if p == "HIGH":
                                    high_leads += 1
                                elif p == "MEDIUM":
                                    medium_leads += 1
                    except Exception:
                        pass

                # Count from conversations.json (tracker)
                total_convs = 0
                qualified = 0
                opted_out = 0
                if os.path.exists("conversations.json"):
                    try:
                        with open("conversations.json", "r", encoding="utf-8") as f:
                            convs = json.load(f)
                            total_convs = len(convs)
                            for c in convs.values():
                                st = c.get("stage", "")
                                if st == "QUALIFIED":
                                    qualified += 1
                                elif st == "OPTED_OUT":
                                    opted_out += 1
                    except Exception:
                        pass

                reply = (
                    "📊 <b>Bot Status Report</b>\n\n"
                    f"<b>Total Leads Scraped:</b> {total_leads}\n"
                    f"🔥 High Priority: {high_leads}\n"
                    f"⚡ Medium Priority: {medium_leads}\n\n"
                    f"<b>Conversations Tracked:</b> {total_convs}\n"
                    f"✅ Qualified (Confirm): {qualified}\n"
                    f"⊘ Opted Out: {opted_out}\n"
                )
                send_message(reply)

            elif cmd == "/leads":
                leads_list = []
                if os.path.exists("leads.csv"):
                    try:
                        with open("leads.csv", "r", encoding="utf-8") as f:
                            rdr = csv.DictReader(f)
                            for row in rdr:
                                if row.get("priority") in ("HIGH", "MEDIUM"):
                                    leads_list.append(row)
                    except Exception:
                        pass

                # Sort or get the last 5 (most recent)
                recent_leads = leads_list[-5:] if len(leads_list) > 5 else leads_list
                recent_leads.reverse() # show latest first

                if not recent_leads:
                    reply = "ℹ️ No hot leads found in leads.csv yet."
                else:
                    reply = "🔥 <b>Recent Hot Leads:</b>\n\n"
                    for idx, lead in enumerate(recent_leads, 1):
                        name = lead.get("name", "Unknown")
                        score = lead.get("website_score", "0")
                        pri = "🔥" if lead.get("priority") == "HIGH" else "⚡"
                        site = lead.get("website", "No site")
                        reply += f"{idx}. {pri} <b>{escape_html(name)}</b> (Score: {score})\n🌐 {escape_html(site)}\n\n"

                send_message(reply)

            elif cmd == "/replies":
                replies_list = []
                if os.path.exists("replied_log.csv"):
                    try:
                        with open("replied_log.csv", "r", encoding="utf-8") as f:
                            rdr = csv.DictReader(f)
                            for row in rdr:
                                replies_list.append(row)
                    except Exception:
                        pass

                recent_replies = replies_list[-5:] if len(replies_list) > 5 else replies_list
                recent_replies.reverse()

                if not recent_replies:
                    reply = "ℹ️ No client replies logged yet."
                else:
                    reply = "📨 <b>Recent Client Replies:</b>\n\n"
                    for idx, rep in enumerate(recent_replies, 1):
                        date = rep.get("date", "")
                        sender = rep.get("sender", "")
                        intent = rep.get("intent", "")
                        reply += f"{idx}. <b>{escape_html(sender)}</b>\n📅 {date} | Intent: <code>{intent}</code>\n\n"

                send_message(reply)

        if new_last_id > last_id:
            with open(state_file, "w") as f:
                json.dump({"last_processed_update_id": new_last_id}, f)

    except Exception as e:
        print(f"  [Telegram Commands] Error processing commands: {e}")
