import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Configure stdout encoding
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

print("====================================================")
print("       LOCAL TELEGRAM & TWILIO TEST SCRIPT          ")
print("====================================================")

# ── Test Telegram ──────────────────────────────────────────────────

print("\n--- 1. Testing Telegram Bot ---")
bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

print(f"Bot Token: {'Set' if bot_token and 'paste' not in bot_token else 'NOT SET'}")
print(f"Chat ID: {'Set' if chat_id and 'paste' not in chat_id else 'NOT SET'}")

if bot_token and chat_id and "paste" not in bot_token and "paste" not in chat_id:
    try:
        import requests
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        text = "🤖 <b>Agency Bot Connection Test</b>\n\nHello Sandeep! If you see this, your local Telegram alerts are working perfectly! 🎉"
        
        print("Sending test Telegram message...")
        resp = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
        
        if resp.status_code == 200:
            print("✅ SUCCESS! Telegram message sent. Check your Telegram chat.")
        else:
            print(f"❌ FAILED! Telegram API returned status code {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"❌ FAILED! Error sending Telegram message: {e}")
else:
    print("⚠️ Skipped Telegram test. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env first.")

# ── Test Twilio ────────────────────────────────────────────────────

print("\n--- 2. Testing Twilio Outbound Call ---")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN", "")
twilio_from = os.getenv("TWILIO_FROM_NUMBER", "")
sandeep_phone = "+919390730129"

print(f"Account SID: {'Set' if twilio_sid else 'NOT SET'}")
print(f"Auth Token: {'Set' if twilio_token else 'NOT SET'}")
print(f"From Number: {'Set' if twilio_from else 'NOT SET'}")

if twilio_sid and twilio_token and twilio_from:
    try:
        from twilio.rest import Client
        print(f"Connecting to Twilio and calling your phone ({sandeep_phone})...")
        client = Client(twilio_sid, twilio_token)
        
        tts_message = "Hello Sandeep, this is a test call from your local Agency Bot. Your Twilio voice alert system is configured successfully."
        twiml_content = f"<Response><Say voice='alice' language='en-IN'>{tts_message}</Say></Response>"
        
        call = client.calls.create(
            to=sandeep_phone,
            from_=twilio_from,
            twiml=twiml_content
        )
        print(f"✅ SUCCESS! Twilio Call placed successfully. SID: {call.sid}")
        print("Your phone should ring in a few seconds!")
    except Exception as e:
        print(f"❌ FAILED! Twilio call error: {e}")
else:
    print("⚠️ Skipped Twilio call test. Please set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER in .env first.")

print("\n====================================================")
