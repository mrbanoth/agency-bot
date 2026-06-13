"""
website_audit.py
Audits a prospect's website and generates a personalised 3-point sales pitch.

RUN:
    python website_audit.py https://target.com "Business Name"

WITH AI PITCH (optional — needs OPENAI_API_KEY in .env):
    python website_audit.py https://target.com "Business Name" --ai
"""

import sys
import json
import time
import re
from datetime import datetime

# Configure stdout/stderr to use UTF-8 to prevent encoding crashes on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import requests
from bs4 import BeautifulSoup

from config import OPENAI_API_KEY, YOUR_NAME, YOUR_PHONE, YOUR_PORTFOLIO


# ──────────────────────────────────────────────
# Technical Audit
# ──────────────────────────────────────────────

def audit_website(url: str) -> dict:
    url = url if url.startswith("http") else "https://" + url
    audit = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "issues": [],
        "score": 0,
    }

    try:
        start = time.time()
        resp  = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AuditBot/1.0)"
        })
        load_time = time.time() - start
        soup = BeautifulSoup(resp.text, "html.parser")

        # SSL
        audit["checks"]["ssl"] = url.startswith("https://")
        if not audit["checks"]["ssl"]:
            audit["issues"].append(
                "No HTTPS — Chrome shows 'Not Secure'. Google penalises non-SSL sites."
            )

        # Speed
        audit["checks"]["fast_load"]          = load_time < 3.0
        audit["checks"]["load_time_seconds"]  = round(load_time, 2)
        if not audit["checks"]["fast_load"]:
            audit["issues"].append(
                f"Slow load ({load_time:.1f}s). Google's threshold is 3s. "
                "Slow sites lose ~40% of visitors before they see any content."
            )

        # Mobile
        viewport = soup.find("meta", attrs={"name": "viewport"})
        audit["checks"]["mobile_friendly"] = viewport is not None
        if not audit["checks"]["mobile_friendly"]:
            audit["issues"].append(
                "Not mobile-friendly. 70%+ of Indian users browse on phones — "
                "this site likely breaks on small screens."
            )

        # SEO basics
        title    = soup.find("title")
        meta_d   = soup.find("meta", attrs={"name": "description"})
        audit["checks"]["has_title"]            = bool(title and title.text.strip())
        audit["checks"]["has_meta_description"] = meta_d is not None
        audit["checks"]["title_text"]           = title.text.strip() if title else ""
        if not audit["checks"]["has_title"]:
            audit["issues"].append("No page title — invisible to Google search rankings.")
        if not audit["checks"]["has_meta_description"]:
            audit["issues"].append("No meta description — Google can't preview the site in search results.")

        # Framework
        page_text = resp.text.lower()
        modern    = any(s in page_text for s in ["react", "next.js", "vue", "nuxt", "gatsby"])
        old_tech  = any(s in page_text for s in ["jquery-1.", "jquery-2.", "wp-content", "joomla"])
        audit["checks"]["modern_framework"]  = modern
        audit["checks"]["old_tech_detected"] = old_tech
        if old_tech:
            audit["issues"].append(
                "Outdated tech detected (WordPress/old jQuery). "
                "Hard to update, slower, higher security risk."
            )
        elif not modern:
            audit["issues"].append(
                "No modern framework — likely a static HTML/legacy CMS site. "
                "Owner can't update it without a developer."
            )

        # Contact / CTA
        has_phone = bool(
            soup.find("a", href=lambda h: h and "tel:" in h) or
            re.search(r"\+91[\s-]?\d{10}|\b[6-9]\d{9}\b", resp.text)
        )
        has_cta = any(w in page_text for w in ["contact us", "get a quote", "book now", "call us", "enquire"])
        audit["checks"]["has_phone"] = has_phone
        audit["checks"]["has_cta"]   = has_cta
        if not has_phone:
            audit["issues"].append("No visible phone number — customers can't call directly.")
        if not has_cta:
            audit["issues"].append("No Call-To-Action — visitors don't know what to do next.")

        # Score
        passing = sum([
            audit["checks"]["ssl"],
            audit["checks"]["fast_load"],
            audit["checks"]["mobile_friendly"],
            audit["checks"]["has_title"],
            audit["checks"]["has_meta_description"],
            audit["checks"]["modern_framework"],
            audit["checks"]["has_phone"],
            audit["checks"]["has_cta"],
        ])
        audit["score"] = round((passing / 8) * 100)

    except Exception as e:
        audit["issues"].append(f"Could not reach site: {e}")

    return audit


# ──────────────────────────────────────────────
# Pitch Generator
# ──────────────────────────────────────────────

ISSUE_PITCHES = {
    "No HTTPS":          ("No Secure Connection",
                          "Your site shows 'Not Secure' in Chrome — this kills trust and Google rankings."),
    "Slow load":         ("Slow Loading Speed",
                          "A slow site loses ~40% of visitors before they even see your content."),
    "Not mobile":        ("Not Optimised for Mobile",
                          "70%+ of your customers browse on phones. This site likely breaks on small screens."),
    "No page title":     ("Missing SEO Basics",
                          "Without a page title, Google can't rank or display your site properly."),
    "No visible phone":  ("No Click-to-Call",
                          "There's no phone number customers can tap from their phone. You're losing enquiries."),
    "No Call-To-Action": ("No Clear Next Step",
                          "Visitors don't know what to do. A 'Get a Free Quote' button alone can double enquiries."),
    "Outdated tech":     ("Outdated Technology",
                          "Built on old tech — slow, hard to update, and a security risk."),
    "No modern":         ("No Modern Framework",
                          "Owner can't update the site without hiring a developer every time."),
}

def generate_pitch(business_name: str, audit: dict, use_ai: bool = False) -> str:
    if use_ai and OPENAI_API_KEY:
        return _ai_pitch(business_name, audit)
    return _rule_pitch(business_name, audit)


def _rule_pitch(business_name: str, audit: dict) -> str:
    lines = []
    n = 1
    for issue in audit["issues"][:3]:
        matched = False
        for key, (title, desc) in ISSUE_PITCHES.items():
            if key.lower() in issue.lower():
                lines.append(f"POINT {n}: {title}\n  → {desc}")
                matched = True
                break
        if not matched:
            lines.append(f"POINT {n}: Website Issue\n  → {issue}")
        n += 1
    return "\n\n".join(lines)


def _ai_pitch(business_name: str, audit: dict) -> str:
    import openai
    openai.api_key = OPENAI_API_KEY
    issues_text = "\n".join(f"- {i}" for i in audit["issues"][:3])
    prompt = f"""
You are a friendly web developer writing a short pitch to a local business owner.
Business: {business_name} | Website: {audit['url']} | Score: {audit['score']}/100
Top Issues:
{issues_text}

Write a 3-point improvement pitch that is warm (not salesy), names specific issues,
explains customer impact, and mentions a modern Next.js rebuild as the fix.
Under 150 words. Format as POINT 1/2/3 with title and 1-2 sentence explanation.
"""
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()


# ──────────────────────────────────────────────
# Report
# ──────────────────────────────────────────────

def print_report(business_name: str, audit: dict, pitch: str):
    priority = ("🔥 Hot lead"  if audit["score"] < 40 else
                "⚡ Warm lead" if audit["score"] < 70 else
                "✅ Skip")

    print(f"\n{'='*60}")
    print(f"  WEBSITE AUDIT — {business_name}")
    print(f"  URL   : {audit['url']}")
    print(f"  Score : {audit['score']}/100  ({priority})")
    print(f"{'='*60}")

    print("\n📋 ISSUES FOUND:")
    for issue in audit["issues"]:
        print(f"  • {issue}")

    print(f"\n✉️  3-POINT PITCH FOR {business_name.upper()}:")
    print("-" * 60)
    print(pitch)
    print("-" * 60)

    print(f"\n📨 SUGGESTED EMAIL SUBJECT:")
    if audit["score"] < 40:
        print(f'  "Quick question about {business_name}\'s website"')
    else:
        print(f'  "A few ideas to get more customers from {business_name}\'s website"')

    print(f"\n💡 NEXT ACTION:")
    if audit["checks"].get("has_phone"):
        print("  → WhatsApp or call them with this pitch")
    else:
        print("  → Find owner on LinkedIn / Google Business and send email")

    print(f"\n  — {YOUR_NAME} | {YOUR_PHONE} | {YOUR_PORTFOLIO}\n")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python website_audit.py <url> [business_name] [--ai]")
        print("Example: python website_audit.py https://clinic.in 'City Dental' --ai")
        sys.exit(1)

    url           = sys.argv[1]
    business_name = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else url
    use_ai        = "--ai" in sys.argv

    print(f"\nAuditing {url} ...")
    audit = audit_website(url)

    print("Generating pitch ...")
    pitch = generate_pitch(business_name, audit, use_ai=use_ai)

    print_report(business_name, audit, pitch)

    fname = f"audit_{business_name.replace(' ', '_')[:30]}_{datetime.now():%Y%m%d_%H%M}.json"
    with open(fname, "w") as f:
        json.dump({"business": business_name, "audit": audit, "pitch": pitch}, f, indent=2)
    print(f"Full audit saved → {fname}\n")


if __name__ == "__main__":
    main()
