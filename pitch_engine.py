"""
pitch_engine.py
Generates personalised 3-point sales pitches using Groq's FREE AI
(llama-3.3-70b — 14,400 req/day free, no credit card needed).
Falls back to rule-based pitch if no API key is set.
"""

import sys, os
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from config import GROQ_API_KEY, GROQ_MODEL, YOUR_NAME, YOUR_PHONE, YOUR_PORTFOLIO

# ── Rule-based fallback (works with zero API keys) ────────────
ISSUE_MAP = {
    "No website":       ("No Online Presence",
                         "Customers searching Google for your services literally cannot find you — "
                         "you're invisible to ~80% of new customers."),
    "No HTTPS":         ("Not Secure Warning",
                         "Chrome shows 'Not Secure' to every visitor. This destroys trust before "
                         "they even read a word."),
    "Slow load":        ("Site Loads Too Slowly",
                         "A slow site loses 40% of visitors in the first 3 seconds. "
                         "Speed is directly tied to how many enquiries you get."),
    "Not mobile":       ("Broken on Mobile Phones",
                         "70%+ of customers browse on phones. If the site breaks on mobile, "
                         "they leave immediately and call your competitor."),
    "No page title":    ("Invisible to Google",
                         "Without a page title, Google cannot rank or display your site. "
                         "You're missing free search traffic every single day."),
    "No phone":         ("No Click-to-Call",
                         "There is no phone number customers can tap to call you instantly. "
                         "Every missed tap is a lost enquiry."),
    "No Call-To-Action":("No Clear Next Step",
                         "Visitors don't know what to do on the site. Adding one 'Get a Free Quote' "
                         "button can double enquiry rates overnight."),
    "Outdated":         ("Built on Outdated Tech",
                         "Old tech means slow speeds, security risks, and you need a developer "
                         "just to change a phone number."),
    "No modern":        ("Cannot Update Without a Developer",
                         "The site has no CMS — every small change needs an expensive developer. "
                         "A modern site lets you update it yourself in minutes."),
}


def _rule_based_pitch(business_name: str, issues: list) -> str:
    lines = []
    n = 1
    for issue in issues[:3]:
        matched = False
        for key, (title, desc) in ISSUE_MAP.items():
            if key.lower() in issue.lower():
                lines.append(f"POINT {n}: {title}\n   {desc}")
                matched = True
                break
        if not matched:
            lines.append(f"POINT {n}: Website Issue Detected\n   {issue}")
        n += 1
    return "\n\n".join(lines)


def _groq_pitch(business_name: str, url: str, score: int, issues: list) -> str:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        issues_text = "\n".join(f"- {i}" for i in issues[:3])
        prompt = f"""You are a friendly Indian freelance web developer writing a short sales pitch.

Business: {business_name}
Website: {url or "No website found"}
Website Quality Score: {score}/100

Top Issues Found:
{issues_text}

Write a 3-point improvement pitch. Rules:
- Warm and conversational, not corporate or salesy
- Name each specific issue and its real-world impact on customers/revenue  
- End by hinting that you can fix this with a fast Next.js website
- Under 120 words total
- Format exactly as:
POINT 1: [Title] — [1-2 sentences]
POINT 2: [Title] — [1-2 sentences]
POINT 3: [Title] — [1-2 sentences]"""

        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [Groq fallback] {e}")
        return _rule_based_pitch(business_name, issues)


def generate_pitch(business_name: str, url: str, score: int, issues: list) -> str:
    """Returns a 3-point pitch string. Uses Groq if key set, else rule-based."""
    if GROQ_API_KEY:
        return _groq_pitch(business_name, url, score, issues)
    return _rule_based_pitch(business_name, issues)
