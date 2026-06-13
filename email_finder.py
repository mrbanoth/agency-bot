"""
email_finder.py
Finds a business contact email from their website.
Uses 3 free methods — no paid API needed.
"""

import re, sys, time, requests
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

SKIP_DOMAINS = {
    "example.com","sentry.io","wixpress.com","google.com",
    "facebook.com","instagram.com","twitter.com","youtube.com",
    "jquery.com","w3.org","schema.org","amazonaws.com",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def _clean(emails: list, site_domain: str) -> list:
    results = []
    for e in emails:
        domain = e.split("@")[-1].lower()
        if domain in SKIP_DOMAINS: continue
        if domain.endswith(".png") or domain.endswith(".jpg"): continue
        if site_domain and domain not in site_domain and site_domain not in domain: continue
        results.append(e.lower())
    return list(dict.fromkeys(results))  # dedupe, preserve order


def _scrape_emails_from_url(url: str, site_domain: str) -> list:
    try:
        r = requests.get(url, timeout=7, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")
        # mailto links first (most reliable)
        emails = []
        for a in soup.find_all("a", href=True):
            if "mailto:" in a["href"].lower():
                e = a["href"].lower().replace("mailto:", "").split("?")[0].strip()
                if "@" in e: emails.append(e)
        # regex fallback on visible text
        if not emails:
            emails = EMAIL_RE.findall(r.text)
        return _clean(emails, site_domain)
    except Exception:
        return []


def find_email(website: str, business_name: str = "") -> str:
    """
    Returns best contact email found, or empty string.
    Tries: homepage → /contact → /about → common patterns
    """
    if not website:
        return ""

    url = website if website.startswith("http") else "https://" + website
    try:
        domain = url.split("//")[-1].split("/")[0].replace("www.", "")
    except Exception:
        return ""

    # Method 1: homepage
    emails = _scrape_emails_from_url(url, domain)
    if emails: return emails[0]
    time.sleep(0.3)

    # Method 2: /contact and /about pages
    for path in ["/contact", "/contact-us", "/about", "/about-us"]:
        emails = _scrape_emails_from_url(url.rstrip("/") + path, domain)
        if emails: return emails[0]
        time.sleep(0.3)

    # Method 3: common patterns (info@ contact@ hello@ etc.)
    for prefix in ["info", "contact", "hello", "support", "business", "enquiry"]:
        candidate = f"{prefix}@{domain}"
        try:
            # Quick SMTP check — does the mail server accept this address?
            import smtplib, dns.resolver
            mx = str(dns.resolver.resolve(domain, "MX")[0].exchange)
            with smtplib.SMTP(mx, 25, timeout=5) as s:
                s.ehlo("check.local")
                s.mail("check@check.local")
                code, _ = s.rcpt(candidate)
                if code == 250:
                    return candidate
        except Exception:
            pass

    # Fallback: return most common pattern even unverified
    return f"info@{domain}"
