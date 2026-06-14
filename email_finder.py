"""
email_finder.py — Finds real contact emails from business websites.

Strategy (in order):
  1. Scan homepage for mailto: links (most reliable)
  2. Scan /contact, /contact-us, /reach-us, /connect, /enquiry pages
  3. Scan /about, /about-us pages
  4. Regex scan full page text for email patterns
  5. Try to verify common prefixes (info@, contact@) via DNS MX check
  6. Return empty string if nothing found — never returns a guessed email
     that can't be verified (avoids bounces that hurt Gmail reputation)
"""

import re, sys, time, socket
import requests
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Domains that commonly appear in page source but are NOT real contact emails
SKIP_DOMAINS = {
    "example.com", "sentry.io", "wixpress.com", "google.com", "googletagmanager.com",
    "facebook.com", "instagram.com", "twitter.com", "youtube.com", "tiktok.com",
    "jquery.com", "w3.org", "schema.org", "amazonaws.com", "cloudfront.net",
    "wordpress.com", "wordpress.org", "gravatar.com", "wp.com",
    "bootstrapcdn.com", "jsdelivr.net", "unpkg.com", "cdnjs.cloudflare.com",
    "fontawesome.com", "fonts.googleapis.com", "gstatic.com",
    "squarespace.com", "wix.com", "weebly.com", "shopify.com",
    "doubleclick.net", "analytics.google.com", "hotjar.com",
    "mailchimp.com", "hubspot.com", "intercom.io",
    "noreply.com", "no-reply.com",
}

SKIP_PREFIXES = {
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "mailer", "bounce", "postmaster", "webmaster",
    "admin", "root", "test",
}

# Contact page paths to try, in priority order
CONTACT_PATHS = [
    "/contact", "/contact-us", "/contactus",
    "/reach-us", "/reach", "/connect",
    "/enquiry", "/enquire", "/get-in-touch",
    "/about", "/about-us", "/aboutus",
    "/team",
]

COMMON_PREFIXES = ["info", "contact", "hello", "enquiry", "enquiries", "sales", "business"]


def _is_valid_email(email: str, site_domain: str) -> bool:
    """Filter out junk emails."""
    if not email or "@" not in email:
        return False
    local, domain = email.lower().rsplit("@", 1)
    if domain in SKIP_DOMAINS:
        return False
    if local in SKIP_PREFIXES:
        return False
    if domain.endswith((".png", ".jpg", ".gif", ".svg", ".css", ".js")):
        return False
    if len(local) < 2 or len(domain) < 4:
        return False
    # Must be on the same domain as the website (or a sub/variant of it)
    if site_domain:
        base = site_domain.replace("www.", "")
        dom_base = domain.replace("www.", "")
        if base not in dom_base and dom_base not in base:
            return False
    return True


def _extract_emails(html: str, site_domain: str) -> list:
    """Pull emails from HTML, prioritising mailto: links."""
    soup   = BeautifulSoup(html, "html.parser")
    emails = []

    # 1. mailto: links are most reliable
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if "mailto:" in href:
            raw = href.replace("mailto:", "").split("?")[0].strip()
            if "@" in raw and _is_valid_email(raw, site_domain):
                emails.append(raw)

    if emails:
        return list(dict.fromkeys(emails))

    # 2. Regex scan full text
    for match in EMAIL_RE.findall(html):
        if _is_valid_email(match.lower(), site_domain):
            emails.append(match.lower())

    return list(dict.fromkeys(emails))


def _fetch(url: str) -> str:
    """Fetch URL, return HTML or empty string."""
    try:
        r = requests.get(url, timeout=7, headers=HEADERS)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return ""


def _verify_mx(domain: str) -> bool:
    """Quick check: does this domain have MX records (can receive email)?"""
    try:
        import dns.resolver
        dns.resolver.resolve(domain, "MX")
        return True
    except Exception:
        pass
    # Fallback: socket lookup
    try:
        socket.getaddrinfo(domain, 25)
        return True
    except Exception:
        return False


def find_email(website: str, business_name: str = "") -> str:
    """
    Returns best contact email found, or "" if nothing reliable found.
    Never returns a guessed/unverified email — avoids Gmail bounces.
    """
    if not website:
        return ""

    url = website if website.startswith("http") else "https://" + website
    try:
        domain = url.split("//")[-1].split("/")[0].lower().replace("www.", "")
    except Exception:
        return ""

    # ── Step 1: Homepage ──────────────────────────────────────
    html = _fetch(url)
    if html:
        emails = _extract_emails(html, domain)
        if emails:
            return emails[0]

    time.sleep(0.2)

    # ── Step 2: Contact and About pages ──────────────────────
    for path in CONTACT_PATHS:
        html = _fetch(url.rstrip("/") + path)
        if html:
            emails = _extract_emails(html, domain)
            if emails:
                return emails[0]
        time.sleep(0.15)

    # ── Step 3: Verify common prefixes via MX check ───────────
    # Only attempt if domain has valid MX records
    if _verify_mx(domain):
        try:
            import smtplib, dns.resolver
            mx_record = str(dns.resolver.resolve(domain, "MX")[0].exchange)
            for prefix in COMMON_PREFIXES:
                candidate = f"{prefix}@{domain}"
                try:
                    with smtplib.SMTP(mx_record, 25, timeout=5) as s:
                        s.ehlo("verify.local")
                        s.mail("v@verify.local")
                        code, _ = s.rcpt(candidate)
                        if code == 250:
                            return candidate
                except Exception:
                    continue
        except Exception:
            pass

    # ── Nothing found — return empty (don't guess) ────────────
    return ""
