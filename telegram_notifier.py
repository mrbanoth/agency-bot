import sys
import requests
import tracker
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
                    "🤖 <b>Agency Bot CRM — Commands</b>\n\n"
                    "📋 <b>Pipeline</b>\n"
                    "/pipeline — Funnel view (counts per stage)\n"
                    "/hot — Active HIGH-priority leads to chase\n"
                    "/clients — Recently scraped hot leads\n"
                    "/stats — Full bot performance stats\n\n"
                    "🔍 <b>Lead lookup</b>\n"
                    "/lead &lt;name or email&gt; — Full lead card + notes\n\n"
                    "✍️ <b>Manage a lead</b>\n"
                    "/note &lt;email&gt; &lt;text&gt; — Add a note\n"
                    "/close &lt;email&gt; &lt;amount&gt; — Mark deal WON 🎉\n"
                    "/lost &lt;email&gt; — Mark deal lost\n\n"
                    "💰 <b>Money</b>\n"
                    "/earnings — Real + potential revenue\n"
                    "/projects — Confirmed/qualified projects\n\n"
                    "<b>/help</b> — Show this message"
                )
                send_message(reply)

            elif cmd == "/pipeline":
                counts = tracker.pipeline_counts()
                stage_icons = {
                    "COLD_SENT": "📧", "FOLLOW_UP_SENT": "📩", "SECOND_FOLLOWUP_SENT": "📨",
                    "REPLIED": "💬", "QUALIFIED": "🏆", "HANDOFF": "🙋",
                    "OPTED_OUT": "🚫", "CLOSED_WON": "✅", "CLOSED_LOST": "❌",
                }
                if not counts:
                    reply = "ℹ️ No leads in the pipeline yet."
                else:
                    reply = "📊 <b>Pipeline Funnel</b>\n\n"
                    order = ["COLD_SENT","FOLLOW_UP_SENT","SECOND_FOLLOWUP_SENT","REPLIED",
                              "QUALIFIED","HANDOFF","CLOSED_WON","CLOSED_LOST","OPTED_OUT"]
                    for stage in order:
                        if stage in counts:
                            reply += f"{stage_icons.get(stage,'•')} <b>{stage}</b>: {counts[stage]}\n"
                    reply += f"\n<b>Total tracked: {sum(counts.values())}</b>"
                send_message(reply)

            elif cmd == "/hot":
                convs = tracker.get_all()
                active_hot = [
                    (email, d) for email, d in convs.items()
                    if d.get("priority") == "HIGH" and tracker.is_active(d)
                ]
                active_hot.sort(key=lambda x: x[1].get("last_contact",""), reverse=True)
                if not active_hot:
                    reply = "ℹ️ No active HIGH-priority leads right now."
                else:
                    reply = f"🔥 <b>Active Hot Leads ({len(active_hot)}):</b>\n\n"
                    for email, d in active_hot[:10]:
                        reply += (
                            f"• <b>{escape_html(d.get('business_name','Unknown'))}</b> "
                            f"({escape_html(d.get('city',''))}) — {d.get('stage','')}\n"
                            f"  📧 <code>{escape_html(email)}</code>\n"
                        )
                send_message(reply)

            elif cmd == "/lead":
                query = text[len(cmd):].strip()
                if not query:
                    send_message("ℹ️ Usage: /lead <name or email>")
                else:
                    found_email, d = tracker.find_by_query(query)
                    if not d:
                        reply = f"❌ No lead found matching \"{escape_html(query)}\""
                    else:
                        notes = d.get("notes", [])
                        notes_text = "\n".join(
                            f"  📝 {escape_html(n.get('date',''))}: {escape_html(n.get('text',''))}"
                            for n in notes
                        ) or "  (no notes yet)"
                        reply = (
                            f"📇 <b>{escape_html(d.get('business_name','Unknown'))}</b>\n\n"
                            f"<b>Stage:</b> {escape_html(d.get('stage',''))}\n"
                            f"<b>Priority:</b> {escape_html(d.get('priority',''))}\n"
                            f"<b>Category:</b> {escape_html(d.get('category',''))}\n"
                            f"<b>City:</b> {escape_html(d.get('city',''))}\n"
                            f"<b>Email:</b> <code>{escape_html(found_email)}</code>\n"
                            f"<b>Phone:</b> {escape_html(d.get('phone','—'))}\n"
                            f"<b>Website:</b> {escape_html(d.get('website','—'))}\n"
                            f"<b>Deal value:</b> ₹{d.get('deal_value',0):,}\n"
                            f"<b>Last contact:</b> {escape_html(d.get('last_contact',''))}\n\n"
                            f"<b>Notes:</b>\n{notes_text}"
                        )
                    send_message(reply)

            elif cmd == "/note":
                parts = text[len(cmd):].strip().split(maxsplit=1)
                if len(parts) < 2 or "@" not in parts[0]:
                    send_message("ℹ️ Usage: /note <email> <note text>")
                else:
                    target_email, note_text = parts[0], parts[1]
                    if tracker.add_note(target_email, note_text):
                        send_message(f"✅ Note added for <code>{escape_html(target_email)}</code>")
                    else:
                        send_message(f"❌ No lead found with email {escape_html(target_email)}")

            elif cmd == "/close":
                parts = text[len(cmd):].strip().split()
                if len(parts) < 2 or "@" not in parts[0] or not parts[1].isdigit():
                    send_message("ℹ️ Usage: /close <email> <amount in INR>")
                else:
                    target_email, amount = parts[0], int(parts[1])
                    if tracker.close_deal(target_email, amount):
                        send_message(
                            f"🎉🤑 <b>DEAL WON!</b> ₹{amount:,} from <code>{escape_html(target_email)}</code>.\n"
                            f"Go build it and get paid! 💪"
                        )
                    else:
                        send_message(f"❌ No lead found with email {escape_html(target_email)}")

            elif cmd == "/lost":
                target_email = text[len(cmd):].strip()
                if not target_email or "@" not in target_email:
                    send_message("ℹ️ Usage: /lost <email>")
                elif tracker.mark_lost(target_email):
                    send_message(f"📉 Marked <code>{escape_html(target_email)}</code> as lost. Moving on!")
                else:
                    send_message(f"❌ No lead found with email {escape_html(target_email)}")

            elif cmd == "/stats":
                import csv as _csv, os as _os
                def _count_rows(path):
                    if not _os.path.exists(path): return 0
                    with open(path, "r", encoding="utf-8") as f:
                        return sum(1 for _ in _csv.DictReader(f))
                scraped  = _count_rows("leads.csv")
                emailed  = _count_rows("sent_log.csv")
                replied  = _count_rows("replied_log.csv")
                counts   = tracker.pipeline_counts()
                won      = counts.get("CLOSED_WON", 0)
                revenue  = tracker.total_revenue()
                reply = (
                    "📈 <b>Agency Bot — Performance Stats</b>\n\n"
                    f"🔎 Leads scraped: <b>{scraped}</b>\n"
                    f"📧 Cold emails sent: <b>{emailed}</b>\n"
                    f"💬 Replies received: <b>{replied}</b>\n"
                    f"🏆 Qualified: <b>{counts.get('QUALIFIED',0)}</b>\n"
                    f"✅ Deals won: <b>{won}</b>\n"
                    f"❌ Deals lost: <b>{counts.get('CLOSED_LOST',0)}</b>\n\n"
                    f"💰 <b>Total revenue: ₹{revenue:,}</b>"
                )
                send_message(reply)

            elif cmd == "/projects":
                qualified_leads = []
                if os.path.exists("conversations.json"):
                    try:
                        with open("conversations.json", "r", encoding="utf-8") as f:
                            convs = json.load(f)
                            for email, c in convs.items():
                                if c.get("stage") == "QUALIFIED":
                                    biz = c.get("business_name") or "Unknown Business"
                                    city = c.get("city") or "Hyderabad"
                                    phone = c.get("phone") or "—"
                                    qualified_leads.append(
                                        f"• <b>{escape_html(biz)}</b> ({escape_html(city)})\n"
                                        f"  📧 Email: <code>{escape_html(email)}</code>\n"
                                        f"  📞 Phone: <code>{escape_html(phone)}</code>\n"
                                    )
                    except Exception:
                        pass

                if not qualified_leads:
                    reply = "ℹ️ No projects confirmed yet. Keep checking!"
                else:
                    reply = f"🏆 <b>Confirmed Freelance Projects ({len(qualified_leads)} total):</b>\n\n"
                    reply += "\n".join(qualified_leads)

                send_message(reply)

            elif cmd == "/earnings" or cmd == "/money":
                counts = tracker.pipeline_counts()
                won_revenue = tracker.total_revenue()
                won_count   = counts.get("CLOSED_WON", 0)
                qualified_count = counts.get("QUALIFIED", 0)
                est_per_site = 15000
                potential_revenue = qualified_count * est_per_site

                reply = (
                    "💰 <b>Freelance Earnings Report</b>\n\n"
                    f"✅ Deals closed: <b>{won_count}</b>\n"
                    f"💵 <b>Real earnings so far: ₹{won_revenue:,} INR</b>\n\n"
                    f"🏆 In pipeline (qualified, not yet closed): <b>{qualified_count}</b>\n"
                    f"🏷️ Est. rate: ₹{est_per_site:,}/site\n"
                    f"📈 <b>Potential if all close: ₹{potential_revenue:,} INR</b>\n\n"
                    "🚀 <i>Use /close &lt;email&gt; &lt;amount&gt; once you land a deal!</i>"
                )
                send_message(reply)

            elif cmd == "/clients" or cmd == "/leads":
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
                    reply = "🔥 <b>Recent Clients to Pitch:</b>\n\n"
                    for idx, lead in enumerate(recent_leads, 1):
                        name = lead.get("name", "Unknown")
                        pri = "🔥" if lead.get("priority") == "HIGH" else "⚡"
                        site = lead.get("website") or "No website"
                        phone = lead.get("phone") or "—"
                        city = lead.get("city") or "—"

                        # Normalize phone for WhatsApp link
                        digits = "".join(filter(str.isdigit, phone))
                        if digits and len(digits) == 10 and digits[0] in "6789":
                            digits = "91" + digits
                        wa_link = f"https://wa.me/{digits}" if digits else ""
                        tel_link = f"tel:{phone}"

                        reply += (
                            f"<b>{idx}. {pri} {escape_html(name)}</b> ({escape_html(city)})\n"
                            f"🌐 Website: {escape_html(site)}\n"
                            f"📞 Phone: <code>{escape_html(phone)}</code>\n"
                            f"📱 WhatsApp: <a href='{wa_link}'>Message</a> | 📞 Call: <a href='{tel_link}'>Dial</a>\n\n"
                        )
                send_message(reply)



        if new_last_id > last_id:
            with open(state_file, "w") as f:
                json.dump({"last_processed_update_id": new_last_id}, f)

    except Exception as e:
        print(f"  [Telegram Commands] Error processing commands: {e}")

def send_no_website_leads(leads):
    """Filter leads with no website but a phone number and send to Sandeep on Telegram."""
    no_site_leads = [l for l in leads if not l.get("website", "").strip() and l.get("phone", "").strip()]
    if not no_site_leads:
        return True

    text = "🔌 <b>CLIENT OPPORTUNITIES (NO WEBSITE)</b> 🔌\n\n"
    text += "The following businesses have no website at all (high-intent web design prospects):\n\n"

    for idx, lead in enumerate(no_site_leads[:10], 1):
        name = lead.get("name", "Unknown")
        phone = lead.get("phone", "—")
        city = lead.get("city", "—")
        category = lead.get("category", "—")
        
        # Normalize phone for WhatsApp link
        digits = "".join(filter(str.isdigit, phone))
        # Handle Indian numbers without country code
        if digits and len(digits) == 10 and digits[0] in "6789":
            digits = "91" + digits
        
        wa_link = f"https://wa.me/{digits}" if digits else ""
        tel_link = f"tel:{phone}"
        
        text += (
            f"<b>{idx}. {escape_html(name)}</b> ({escape_html(category)})\n"
            f"📍 City: {escape_html(city)}\n"
            f"📞 Phone: <code>{escape_html(phone)}</code>\n"
            f"📱 WhatsApp: <a href='{wa_link}'>Message</a> | 📞 Call: <a href='{tel_link}'>Dial</a>\n\n"
        )
    
    if len(no_site_leads) > 10:
        text += f"<i>... and {len(no_site_leads) - 10} more found today. See leads.csv for full list.</i>"

    return send_message(text)
