import os
import csv
import sys
from datetime import datetime, timedelta
from config import (
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER,
    CALL_WINDOW_START, CALL_WINDOW_END, YOUR_PHONE
)

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

CALLS_LOG = "calls_log.csv"

def is_in_call_window() -> bool:
    ist_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
    hour = ist_time.hour
    return CALL_WINDOW_START <= hour < CALL_WINDOW_END

def can_call_today(phone: str) -> bool:
    if not os.path.exists(CALLS_LOG):
        return True
    
    normalized_phone = phone.strip()
    try:
        with open(CALLS_LOG, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("phone", "").strip() == normalized_phone:
                    call_date_str = row.get("date", "")[:10]
                    try:
                        call_date = datetime.strptime(call_date_str, "%Y-%m-%d")
                        days = (datetime.now() - call_date).days
                        if days < 3:
                            return False
                    except Exception:
                        continue
    except Exception:
        pass
    return True

def _log_call(phone: str, name: str, status: str):
    exists = os.path.exists(CALLS_LOG)
    with open(CALLS_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "phone", "business_name", "status"])
        if not exists:
            w.writeheader()
        w.writerow({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "phone": phone,
            "business_name": name,
            "status": status
        })

def call_client(phone: str, business_name: str, city: str) -> bool:
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_FROM_NUMBER:
        print("  [Twilio] Warning: Twilio credentials not fully set. Skipping client call.")
        return False
        
    if not is_in_call_window():
        print(f"  [Twilio] Out of call window ({CALL_WINDOW_START}AM-{CALL_WINDOW_END}PM IST). Skipping call to {business_name}.")
        return False

    if not can_call_today(phone):
        print(f"  [Twilio] Call frequency limit reached: Already called {phone} in the last 3 days. Skipping.")
        return False

    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Indian numbers format check
        to_phone = phone.strip()
        if not to_phone.startswith("+"):
            if to_phone.startswith("91") and len(to_phone) == 12:
                to_phone = "+" + to_phone
            elif len(to_phone) == 10:
                to_phone = "+91" + to_phone

        tts_message = (
            f"Hello, this is a message from Sandeep, a web developer from Hyderabad. "
            f"I recently sent you emails about your website. "
            f"I would love to help your business get more customers online. "
            f"Please call me back on +91 9390730129 or reply to my email. "
            f"Thank you and have a great day."
        )
        
        twiml_content = f"<Response><Say voice='alice' language='en-IN'>{tts_message}</Say></Response>"
        
        call = client.calls.create(
            to=to_phone,
            from_=TWILIO_FROM_NUMBER,
            twiml=twiml_content
        )
        
        _log_call(to_phone, business_name, f"SUCCESS_SID_{call.sid}")
        print(f"  [Twilio] Call placed to {business_name} ({to_phone}). SID: {call.sid}")
        return True
    except Exception as e:
        print(f"  [Twilio] Call failed: {e}")
        _log_call(phone, business_name, f"FAILED_{str(e)[:50]}")
        return False

def call_sandeep(business_name: str, city: str, client_phone: str) -> bool:
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_FROM_NUMBER:
        print("  [Twilio] Warning: Twilio credentials not fully set. Skipping alert call to Sandeep.")
        return False

    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        tts_message = (
            f"Sandeep! Hot lead alert. {business_name} from {city} wants to hire you. "
            f"Their phone number is {client_phone or 'not provided'}. "
            f"Check your Telegram and email now!"
        )

        twiml_content = f"<Response><Say voice='alice' language='en-IN'>{tts_message}</Say></Response>"

        call = client.calls.create(
            to=YOUR_PHONE,
            from_=TWILIO_FROM_NUMBER,
            twiml=twiml_content
        )
        print(f"  [Twilio] Alert call placed to Sandeep. SID: {call.sid}")
        return True
    except Exception as e:
        print(f"  [Twilio] Alert call to Sandeep failed: {e}")
        return False
