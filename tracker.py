"""
tracker.py — Conversation state manager (shared by all modules)

Tracks every lead's journey:
  COLD_SENT → FOLLOW_UP_SENT → REPLIED → QUALIFIED → OPTED_OUT

Single source of truth in conversations.json.
Imported by: outreach_sender, follow_up, reply_checker
"""

import os, json
from datetime import datetime

CONV_FILE = "conversations.json"


def load() -> dict:
    if not os.path.exists(CONV_FILE):
        return {}
    try:
        with open(CONV_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save(data: dict):
    with open(CONV_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def register(lead: dict, email: str):
    """Call when cold email is sent. Creates conversation entry if not exists."""
    convs = load()
    key   = email.lower().strip()
    if key not in convs:
        convs[key] = {
            "business_name":   lead.get("name", ""),
            "category":        lead.get("category", ""),
            "city":            lead.get("city", ""),
            "website":         lead.get("website", ""),
            "phone":           lead.get("phone", ""),
            "priority":        lead.get("priority", ""),
            "issues":          lead.get("website_issues", ""),
            "stage":           "COLD_SENT",
            "exchanges":       0,
            "qualified":       False,
            "follow_up_sent":  False,
            "call_attempted":  False,
            "cold_sent_date":  datetime.now().strftime("%Y-%m-%d"),
            "last_contact":    datetime.now().strftime("%Y-%m-%d"),
        }
        save(convs)


def update(email: str, **kwargs):
    """Update any fields for a lead's conversation."""
    convs = load()
    key   = email.lower().strip()
    if key in convs:
        convs[key].update(kwargs)
    else:
        convs[key] = {**kwargs, "last_contact": datetime.now().strftime("%Y-%m-%d")}
    save(convs)


def get(email: str) -> dict:
    """Get one lead's conversation data."""
    return load().get(email.lower().strip(), {})


def get_all() -> dict:
    """Get all conversation data."""
    return load()


def days_since(date_str: str) -> int:
    """How many days since a YYYY-MM-DD date string."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return (datetime.now() - d).days
    except Exception:
        return 0


def is_active(data: dict) -> bool:
    """Return True if this lead is still in play (not opted out or qualified)."""
    return data.get("stage") not in ("OPTED_OUT", "QUALIFIED", "HANDOFF", "CLOSED")
