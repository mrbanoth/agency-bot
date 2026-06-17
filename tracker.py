"""
tracker.py — Conversation state manager (shared by all modules)

Tracks every lead's journey:
  COLD_SENT → FOLLOW_UP_SENT → REPLIED → QUALIFIED → CLOSED_WON
                                       ↘ OPTED_OUT / CLOSED_LOST

Single source of truth in conversations.json — this IS the CRM database.
Imported by: outreach_sender, follow_up, reply_checker, telegram_notifier
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
            "notes":           [],
            "deal_value":      0,
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
    """Return True if this lead is still in play (not opted out or closed)."""
    return data.get("stage") not in ("OPTED_OUT", "CLOSED_WON", "CLOSED_LOST")


# ── CRM helpers (used by Telegram CRM commands) ────────────────

def find_by_query(query: str) -> tuple:
    """Find a conversation by exact email or partial business-name match.
    Returns (email, data) or (None, None) if nothing matches."""
    query = query.strip().lower()
    if not query:
        return None, None
    convs = load()
    if query in convs:
        return query, convs[query]
    for email, data in convs.items():
        if query in data.get("business_name", "").lower():
            return email, data
    return None, None


def add_note(email: str, text: str) -> bool:
    """Append a timestamped note to a lead's conversation."""
    convs = load()
    key = email.lower().strip()
    if key not in convs:
        return False
    convs[key].setdefault("notes", []).append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": text,
    })
    save(convs)
    return True


def close_deal(email: str, amount: int) -> bool:
    """Mark a lead as a won deal with the agreed price (in INR)."""
    convs = load()
    key = email.lower().strip()
    if key not in convs:
        return False
    convs[key].update({
        "stage": "CLOSED_WON",
        "deal_value": amount,
        "closed_date": datetime.now().strftime("%Y-%m-%d"),
        "last_contact": datetime.now().strftime("%Y-%m-%d"),
    })
    save(convs)
    return True


def mark_lost(email: str) -> bool:
    """Mark a lead as a lost deal (won't be pitched again)."""
    convs = load()
    key = email.lower().strip()
    if key not in convs:
        return False
    convs[key].update({
        "stage": "CLOSED_LOST",
        "last_contact": datetime.now().strftime("%Y-%m-%d"),
    })
    save(convs)
    return True


def pipeline_counts() -> dict:
    """Count leads per pipeline stage."""
    counts = {}
    for data in load().values():
        stage = data.get("stage", "UNKNOWN")
        counts[stage] = counts.get(stage, 0) + 1
    return counts


def total_revenue() -> int:
    """Sum of deal_value across all CLOSED_WON leads."""
    return sum(d.get("deal_value", 0) for d in load().values() if d.get("stage") == "CLOSED_WON")
