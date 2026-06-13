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
CITY            = os.getenv("TARGET_CITY", "Hyderabad")
BUSINESS_TYPES  = [
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
]
MAX_LEADS_PER_RUN = 50
OUTPUT_CSV        = "leads.csv"
LOG_FILE          = "agency_log.txt"

# ─── QUALITY THRESHOLDS ───────────────────────────────────────
HIGH_PRIORITY_SCORE   = 40
MEDIUM_PRIORITY_SCORE = 70

# ─── SCHEDULER ────────────────────────────────────────────────
DAILY_RUN_TIME = "09:00"   # runs every day at 9 AM automatically
