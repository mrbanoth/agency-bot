"""
main.py — Master pipeline (optimized)
  1. Pick TODAY'S city (rotates daily — 1 city per run, no timeout)
  2. Scrape Google Maps (15 business types × 3 leads each = ~45 leads)
  3. Skip big national brands automatically
  4. Audit websites in parallel (3 threads — 3× faster)
  5. Find business email
  6. Generate AI pitch
  7. Send cold emails (max 20/day, auto, with visible logs)
  8. Check inbox for replies
  9. Email YOU a digest
"""

import sys, csv, os, time, traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"): sys.stderr.reconfigure(encoding="utf-8")

from config import (
    CITIES, BUSINESS_TYPES, OUTPUT_CSV, LOG_FILE,
    HIGH_PRIORITY_SCORE, MEDIUM_PRIORITY_SCORE,
    LEADS_PER_CATEGORY, BRAND_BLOCKLIST,
)
from pitch_engine import generate_pitch
from email_finder import find_email
from outreach_sender import run_outreach
from reply_checker import check_replies
from notifier import send_lead_digest, send_error_alert


def log(msg):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line  = f"[{stamp}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── City rotation: 1 city per run, cycles through all cities ──

def pick_today_city() -> str:
    """Rotate through CITIES based on day-of-year so each city runs once every N days."""
    day_index = datetime.now().timetuple().tm_yday
    return CITIES[day_index % len(CITIES)]


# ── Brand blocklist: skip huge national brands ─────────────────

def is_big_brand(name: str, website: str) -> bool:
    name_lower    = (name or "").lower()
    website_lower = (website or "").lower()
    for brand in BRAND_BLOCKLIST:
        if brand in name_lower or brand in website_lower:
            return True
    return False


# ── Website Audit ──────────────────────────────────────────────

def check_website(url):
    import requests, re
    from bs4 import BeautifulSoup

    result = {
        "reachable": False, "has_ssl": False, "fast_load": False,
        "mobile_friendly": False, "modern_framework": False,
        "has_phone": False, "has_cta": False,
        "score": 0, "issues": [],
    }
    if not url:
        result["issues"].append("No website at all")
        return result
    try:
        full = url if url.startswith("http") else "https://" + url
        result["has_ssl"] = full.startswith("https://")
        if not result["has_ssl"]: result["issues"].append("No HTTPS")

        r    = requests.get(full, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        load = r.elapsed.total_seconds()
        result["reachable"] = r.status_code == 200
        result["fast_load"] = load < 3.0
        if not result["fast_load"]: result["issues"].append(f"Slow load ({load:.1f}s)")

        soup = BeautifulSoup(r.text, "html.parser")
        page = r.text.lower()

        vp = soup.find("meta", attrs={"name": "viewport"})
        result["mobile_friendly"] = vp is not None
        if not result["mobile_friendly"]: result["issues"].append("Not mobile-friendly")

        if not (soup.find("title") and soup.find("title").text.strip()):
            result["issues"].append("No page title")
        if not soup.find("meta", attrs={"name": "description"}):
            result["issues"].append("No meta description")

        modern = any(s in page for s in ["react","next.js","vue","nuxt","gatsby"])
        old    = any(s in page for s in ["wp-content","jquery-1.","jquery-2.","joomla"])
        result["modern_framework"] = modern
        if old:         result["issues"].append("Outdated tech (WordPress/old jQuery)")
        elif not modern: result["issues"].append("No modern framework detected")

        result["has_phone"] = bool(
            soup.find("a", href=lambda h: h and "tel:" in h) or
            re.search(r"\+91[\s-]?\d{10}|\b[6-9]\d{9}\b", r.text)
        )
        result["has_cta"] = any(
            w in page for w in ["contact us","get a quote","book now","call us","enquire","whatsapp"]
        )
        if not result["has_phone"]: result["issues"].append("No phone number on site")
        if not result["has_cta"]:   result["issues"].append("No Call-To-Action button")

        result["score"] = sum([
            result["reachable"]        * 15,
            result["has_ssl"]          * 15,
            result["fast_load"]        * 15,
            result["mobile_friendly"]  * 20,
            result["modern_framework"] * 15,
            result["has_phone"]        * 10,
            result["has_cta"]          * 10,
        ])
    except Exception as e:
        result["issues"].append(f"Unreachable: {str(e)[:60]}")
    return result


# ── Google Maps Scraper ────────────────────────────────────────

def scrape_maps(city, btype, max_n):
    import urllib.parse
    from playwright.sync_api import sync_playwright

    leads, query = [], f"{btype} in {city}"
    url = f"https://www.google.com/maps/search/{urllib.parse.quote(query)}"
    log(f"  Scraping: {query}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
            ctx     = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                viewport={"width": 1280, "height": 800},
            )
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)

            panel = page.query_selector('[role="feed"]')
            if panel:
                for _ in range(4):
                    panel.evaluate("el => el.scrollTop += 1200")
                    time.sleep(1.0)

            cards = page.query_selector_all('a[href*="/maps/place/"]')
            seen, urls = set(), []
            for c in cards:
                h = c.get_attribute("href")
                if h and h not in seen:
                    seen.add(h); urls.append(h)
                if len(urls) >= max_n: break

            for place_url in urls:
                try:
                    page.goto(place_url, wait_until="domcontentloaded", timeout=20000)
                    time.sleep(1.5)
                    def t(sel):
                        el = page.query_selector(sel)
                        return el.inner_text().strip() if el else ""
                    name    = t("h1")
                    website = t('[data-item-id="authority"] .fontBodyMedium')

                    # Skip big national brands immediately
                    if is_big_brand(name, website):
                        log(f"    ⊘ {name} — big brand, skipping")
                        continue

                    leads.append({
                        "name":     name,
                        "address":  t('[data-item-id="address"] .fontBodyMedium'),
                        "phone":    t('[data-item-id*="phone"] .fontBodyMedium'),
                        "website":  website,
                        "rating":   t('.F7nice span[aria-hidden]'),
                        "category": btype, "city": city, "maps_url": place_url,
                    })
                    log(f"    ✓ {name} | {website or 'NO SITE'}")
                    time.sleep(0.6)
                except Exception as e:
                    log(f"    ✗ {e}")
            browser.close()
    except Exception as e:
        log(f"  [Maps error] {e}")
    return leads


# ── Enrich one lead (parallel-safe) ───────────────────────────

def enrich_one(lead: dict) -> dict:
    q = check_website(lead.get("website", ""))
    lead["website_score"]  = q["score"]
    lead["website_issues"] = " | ".join(q["issues"])
    lead["priority"] = (
        "HIGH"   if q["score"] < HIGH_PRIORITY_SCORE   else
        "MEDIUM" if q["score"] < MEDIUM_PRIORITY_SCORE else
        "SKIP"
    )
    if lead["priority"] != "SKIP":
        lead["email"] = find_email(lead.get("website", ""), lead.get("name", ""))
        lead["pitch"] = generate_pitch(
            lead.get("name", ""), lead.get("website", ""),
            q["score"], q["issues"]
        )
    else:
        lead["email"] = ""
        lead["pitch"] = ""
    return lead


def enrich_parallel(leads, workers=3):
    """Enrich leads 3 at a time — 3× faster than serial."""
    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(enrich_one, lead): lead for lead in leads}
        for fut in as_completed(futures):
            try:
                result = fut.result()
                name = result.get("name", "?")
                pri  = result.get("priority", "?")
                em   = result.get("email", "")
                icon = "🔥" if pri == "HIGH" else "⚡" if pri == "MEDIUM" else "–"
                log(f"  {icon} {name} | score={result.get('website_score',0)} | email={'✓' if em else '✗'}")
                results.append(result)
            except Exception as e:
                log(f"  [Enrich error] {e}")
    return results


# ── CSV ───────────────────────────────────────────────────────

FIELDS = [
    "priority","name","category","city","phone","email","website",
    "website_score","website_issues","pitch","address","rating","maps_url","date_found",
]

def save_leads(leads):
    existing = set()
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing.add(row.get("name","").strip().lower())

    new = []
    for l in leads:
        if l.get("name","").strip().lower() not in existing and l["priority"] != "SKIP":
            l["date_found"] = datetime.now().strftime("%Y-%m-%d")
            new.append(l)

    if new:
        exists = os.path.exists(OUTPUT_CSV)
        with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
            if not exists: w.writeheader()
            w.writerows(sorted(new, key=lambda x: x.get("website_score", 100)))
        log(f"  Saved {len(new)} new leads → {OUTPUT_CSV}")
    return new


# ── Main ──────────────────────────────────────────────────────

def run():
    today_city = pick_today_city()
    today_date = datetime.now().strftime("%d %b %Y")

    log("=" * 60)
    log(f"  AGENCY BOT  |  {today_city}  |  {today_date}")
    log(f"  Rotation: city {CITIES.index(today_city)+1}/{len(CITIES)}")
    log("=" * 60)

    try:
        all_leads = []

        for btype in BUSINESS_TYPES:
            log(f"\n[Scrape] {btype} in {today_city}")
            raw = scrape_maps(today_city, btype, LEADS_PER_CATEGORY)

            if raw:
                log(f"[Enrich] {len(raw)} leads (parallel) ...")
                scored = enrich_parallel(raw)
                all_leads.extend(scored)

        # ── Stats ──
        high   = [l for l in all_leads if l["priority"] == "HIGH"]
        medium = [l for l in all_leads if l["priority"] == "MEDIUM"]
        hot    = high + medium
        with_email = [l for l in hot if l.get("email","").strip()]

        log(f"\n{'='*60}")
        log(f"  RESULTS FOR {today_city}")
        log(f"  🔥 HIGH priority : {len(high)}")
        log(f"  ⚡ MEDIUM priority: {len(medium)}")
        log(f"  📧 Have email    : {len(with_email)}")
        log(f"  Total scraped   : {len(all_leads)}")
        log(f"{'='*60}")

        new_leads = save_leads(all_leads)
        log(f"  New leads saved : {len(new_leads)}")

        # ── Send cold emails ──
        log("\n[Phase 3] Sending cold emails ...")
        run_outreach(new_leads)

        # ── Check inbox ──
        log("\n[Phase 4] Checking inbox for replies ...")
        check_replies()

        # ── Digest to Sandeep ──
        log("\n[Phase 5] Sending digest to you ...")
        send_lead_digest(new_leads or hot[:20])

        log(f"\n  ✅ DONE — check sandeepnaikb0@gmail.com")
        log("=" * 60)

    except Exception:
        err = traceback.format_exc()
        log(f"  ERROR:\n{err}")
        send_error_alert(err)


if __name__ == "__main__":
    run()
