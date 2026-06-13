"""
lead_scraper.py
Scrapes Google Maps for local businesses, audits their websites,
and exports hot leads to leads.csv.

RUN:
    python lead_scraper.py
"""

import sys
import time
import csv
import urllib.parse
from datetime import datetime

# Configure stdout/stderr to use UTF-8 to prevent encoding crashes on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import requests
from bs4 import BeautifulSoup

from config import (
    CITY, BUSINESS_TYPES, MAX_LEADS_PER_RUN, OUTPUT_CSV,
    HIGH_PRIORITY_SCORE, MEDIUM_PRIORITY_SCORE,
)


# ──────────────────────────────────────────────
# Website Quality Checker
# ──────────────────────────────────────────────

def check_website_quality(url: str) -> dict:
    """Score a website 0-100. Lower = worse site = hotter lead."""
    result = {
        "url": url,
        "reachable": False,
        "has_ssl": False,
        "page_load_ok": False,
        "has_meta_viewport": False,
        "has_modern_framework": False,
        "score": 0,
        "issues": [],
    }

    if not url:
        result["issues"].append("No website at all")
        return result

    try:
        url = url if url.startswith("http") else "https://" + url
        result["has_ssl"] = url.startswith("https://")
        if not result["has_ssl"]:
            result["issues"].append("No HTTPS/SSL")

        resp = requests.get(url, timeout=8, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AuditBot/1.0)"
        })
        result["reachable"] = resp.status_code == 200
        result["page_load_ok"] = resp.elapsed.total_seconds() < 3.0

        if not result["page_load_ok"]:
            result["issues"].append(f"Slow load ({resp.elapsed.total_seconds():.1f}s)")

        soup = BeautifulSoup(resp.text, "html.parser")

        viewport = soup.find("meta", attrs={"name": "viewport"})
        result["has_meta_viewport"] = viewport is not None
        if not result["has_meta_viewport"]:
            result["issues"].append("Not mobile-friendly")

        page_text = resp.text.lower()
        modern_signals = ["react", "next.js", "vue", "angular", "nuxt", "gatsby"]
        result["has_modern_framework"] = any(s in page_text for s in modern_signals)
        if not result["has_modern_framework"]:
            result["issues"].append("No modern JS framework")

        score = 0
        if result["reachable"]:            score += 20
        if result["has_ssl"]:              score += 20
        if result["page_load_ok"]:         score += 20
        if result["has_meta_viewport"]:    score += 20
        if result["has_modern_framework"]: score += 20
        result["score"] = score

    except Exception as e:
        result["issues"].append(f"Unreachable: {str(e)[:60]}")

    return result


# ──────────────────────────────────────────────
# Google Maps Scraper
# ──────────────────────────────────────────────

def scrape_google_maps(city: str, business_type: str, max_results: int = 10) -> list:
    """Scrape Google Maps listings using headless Chrome (Playwright)."""
    from playwright.sync_api import sync_playwright

    leads = []
    query = f"{business_type} in {city}"
    url   = f"https://www.google.com/maps/search/{urllib.parse.quote(query)}"
    print(f"  Searching: {query}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        # Scroll panel to load more listings
        panel = page.query_selector('[role="feed"]')
        if panel:
            for _ in range(5):
                panel.evaluate("el => el.scrollTop += 1000")
                time.sleep(1.5)

        cards = page.query_selector_all('a[href*="/maps/place/"]')
        seen, place_urls = set(), []
        for card in cards:
            href = card.get_attribute("href")
            if href and href not in seen:
                seen.add(href)
                place_urls.append(href)
            if len(place_urls) >= max_results:
                break

        print(f"    Found {len(place_urls)} listings ...")

        for place_url in place_urls:
            try:
                page.goto(place_url, wait_until="domcontentloaded", timeout=20000)
                time.sleep(2)

                def txt(sel):
                    el = page.query_selector(sel)
                    return el.inner_text().strip() if el else ""

                leads.append({
                    "name":     txt("h1"),
                    "address":  txt('[data-item-id="address"] .fontBodyMedium'),
                    "phone":    txt('[data-item-id*="phone"] .fontBodyMedium'),
                    "website":  txt('[data-item-id="authority"] .fontBodyMedium'),
                    "rating":   txt('.F7nice span[aria-hidden]'),
                    "category": business_type,
                    "city":     city,
                    "maps_url": place_url,
                })
                print(f"    ✓ {leads[-1]['name']} | site: {leads[-1]['website'] or 'NONE'}")
            except Exception as e:
                print(f"    ✗ {e}")

        browser.close()

    return leads


# ──────────────────────────────────────────────
# Enrich + Filter
# ──────────────────────────────────────────────

def enrich_leads(raw_leads: list) -> list:
    enriched = []
    for lead in raw_leads:
        print(f"  Auditing: {lead['name']}")
        q = check_website_quality(lead.get("website", ""))
        lead["website_score"]  = q["score"]
        lead["website_issues"] = " | ".join(q["issues"])
        lead["priority"] = (
            "HIGH"   if q["score"] < HIGH_PRIORITY_SCORE   else
            "MEDIUM" if q["score"] < MEDIUM_PRIORITY_SCORE else
            "SKIP"
        )
        enriched.append(lead)
        time.sleep(0.5)
    return enriched


def save_csv(leads: list, filename: str):
    if not leads:
        print("No leads to save.")
        return
    fields = [
        "priority", "name", "category", "city", "phone",
        "website", "website_score", "website_issues",
        "address", "rating", "maps_url",
    ]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted(leads, key=lambda x: x.get("website_score", 100)))
    print(f"\n✅ Saved {len(leads)} leads → {filename}")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f"  LEAD SCRAPER  |  {datetime.now():%Y-%m-%d %H:%M}")
    print(f"  City: {CITY}")
    print(f"{'='*55}\n")

    all_leads = []
    per_cat   = max(1, MAX_LEADS_PER_RUN // len(BUSINESS_TYPES))

    for btype in BUSINESS_TYPES:
        print(f"\n[Scraping] {btype.upper()}")
        raw     = scrape_google_maps(CITY, btype, max_results=per_cat)
        print(f"\n[Auditing] {len(raw)} sites ...")
        scored  = enrich_leads(raw)
        all_leads.extend(scored)

    hot = [l for l in all_leads if l["priority"] != "SKIP"]
    print(f"\n  Total scraped: {len(all_leads)}")
    print(f"  Hot leads    : {len(hot)}")

    save_csv(hot, OUTPUT_CSV)

    print("\n🔥 TOP 5 LEADS:")
    for i, lead in enumerate(sorted(hot, key=lambda x: x.get("website_score", 100))[:5], 1):
        print(f"  {i}. {lead['name']} ({lead['category']})")
        print(f"     Issues : {lead['website_issues']}")
        print(f"     Phone  : {lead['phone'] or 'N/A'}")


if __name__ == "__main__":
    main()
