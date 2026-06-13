"""
config.py — Single source of truth. Only edit this file.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── YOUR DETAILS ─────────────────────────────────────────────
YOUR_NAME       = "Sandeep Naik"
YOUR_PHONE      = "+91 9390730129"
YOUR_PORTFOLIO  = "https://mrbanoth.online"
YOUR_EMAIL      = "sandeepnaikb0@gmail.com"   # all notifications land here

# ─── GMAIL FREE NOTIFICATIONS ─────────────────────────────────
# How to get Gmail App Password (takes 2 min, completely free):
#   1. Go to myaccount.google.com → Security → 2-Step Verification → turn ON
#   2. Search "App passwords" in the same page
#   3. Create one named "AgencyBot" → copy the 16-char password
#   4. Paste it in .env as GMAIL_APP_PASSWORD
GMAIL_ADDRESS      = os.getenv("GMAIL_ADDRESS", YOUR_EMAIL)
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

# ─── GROQ FREE AI ─────────────────────────────────────────────
# 100% free — no credit card needed:
#   1. Go to https://console.groq.com → sign up with Google
#   2. Click "API Keys" → Create → copy key
#   3. Paste in .env as GROQ_API_KEY
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"

# ─── SCRAPER SETTINGS ─────────────────────────────────────────
# Bot rotates through all cities — 1 city per day automatically.
# Day 1 = Hyderabad, Day 2 = Bangalore, etc. Cycles forever.
CITIES = [
    # Tier 1 — highest competition but most leads
    "Hyderabad", "Bangalore", "Mumbai", "Chennai", "Delhi",
    # Tier 2 — good volume
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Surat",
    "Lucknow", "Kanpur", "Nagpur", "Visakhapatnam", "Bhopal",
    # Tier 3 — smaller cities, less competition, easier to close
    "Coimbatore", "Kochi", "Indore", "Vadodara", "Patna",
]

BUSINESS_TYPES = [
    "restaurant",
    "dental clinic",
    "boutique",
    "gym",
    "school",
    "travel agency",
    "chartered accountant",
    "interior designer",
    "coaching classes",
    "NGO",
    "hospital",
    "hotel",
    "real estate agency",
    "event management",
    "bakery",
]

LEADS_PER_CATEGORY = 3    # 3 leads × 15 types = ~45 per city per run
OUTPUT_CSV         = "leads.csv"
LOG_FILE           = "agency_log.txt"

# ─── BRAND BLOCKLIST ──────────────────────────────────────────
# Skip huge national brands — they already have world-class sites.
# Bot focuses on small/medium local businesses that NEED your help.
BRAND_BLOCKLIST = [
    # Hospitals / pharma
    "apollo","yashoda","aster","care hospital","fortis","manipal","narayana",
    "rainbow children","kims","maxcure",
    # Hotels / hospitality
    "marriott","itc hotel","taj hotel","hyatt","hilton","radisson","oberoi",
    "lemon tree","the park hotel",
    # Food chains / QSR
    "mcdonald","kfc","pizza hut","subway","domino","burger king","starbucks",
    "cafe coffee day","barbeque nation",
    # Gym platforms
    "cult.fit","anytime fitness","gold's gym",
    # Travel platforms
    "makemytrip","cleartrip","yatra","goibibo","booking.com","airbnb","thomas cook",
    # Ed-tech
    "byju","unacademy","vedantu","toppr",
    # Banks
    "hdfc","icici","sbi","axis bank","kotak",
    # Retail chains
    "reliance","big bazaar","dmart","lifestyle","shoppers stop",
    # Big websites / aggregators (they have dedicated dev teams)
    "instagram.com","facebook.com","justdial","sulekha","indiamart",
    "zomato","swiggy","amazon","flipkart","myntra","naukri","linkedin",
    "practo","lybrate","1mg","netmeds","dezy.com","riya.travel",
]

# ─── QUALITY THRESHOLDS ───────────────────────────────────────
HIGH_PRIORITY_SCORE   = 40   # score below this = HOT lead
MEDIUM_PRIORITY_SCORE = 70   # score below this = warm lead

# ─── SCHEDULER ────────────────────────────────────────────────
DAILY_RUN_TIME = "09:00"   # local scheduler (backup for non-GitHub runs)
