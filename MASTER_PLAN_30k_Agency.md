# 🚀 Automated Freelance Agency Machine — Master Plan
**Goal:** ₹30,000/month | **Stack:** Next.js · Contentful · Razorpay · Twilio/Tawk.to

---

## THE MATH FIRST

| Package | Price | Clients/Month to Hit ₹30k |
|---------|-------|--------------------------|
| Basic Website (5-page) | ₹15,000 | 2 clients |
| Business Website + CMS | ₹25,000 | 1–2 clients |
| E-commerce / Advanced | ₹40,000 | 1 client |
| Monthly Maintenance | ₹3,000/mo | Stack 5–8 clients over time |

**Realistic path:** 1 × ₹25k project + 1 × basic + 2 maintenance retainers = ₹34k/month.
You need to pitch ~30–40 leads/week to close 1–2/week consistently.

---

## PHASE 1 — LEAD GENERATION MACHINE

### What Makes a Lead "HOT"

Score 0–40 (🔥 HIGH — pitch immediately):
- No website at all
- Website broken or unreachable
- No mobile viewport (breaks on phones)
- No HTTPS
- Load time > 5 seconds

Score 41–69 (⚡ MEDIUM — pitch with softer angle):
- Has a site but no CTA / contact form
- No meta description
- No modern framework

Score 70+ (✅ SKIP — already invested in web)

### Target Business Categories (Ranked by Conversion Rate)

1. Local restaurants / cafes — Almost always have terrible or no websites
2. Dental / medical clinics — Patients search online; doctors care about reputation
3. Coaching classes / tuition centres — Admissions season = urgency
4. Travel agencies — Online bookings = direct revenue link (easy ROI pitch)
5. Boutiques / clothing stores — Visual product = easy demo
6. NGOs — Grant requirements often mandate a website
7. Chartered accountants / lawyers — Professional image matters
8. Interior designers / architects — Portfolio site = their business card

---

## PHASE 2 — OUTREACH

See `outreach_templates.md` for all copy-paste templates.

**Channel priority:**
1. WhatsApp (80–90% open rate) — use if phone number available
2. Email — use Apollo.io / Hunter.io to find owner's email
3. LinkedIn DM — best for CAs, architects, NGO directors

**Sequences:**
- Day 0: Send initial message
- Day 3: Follow-up if no reply
- Day 7: Final follow-up + free mockup offer

---

## PHASE 3 — FOOT-IN-THE-DOOR SYSTEM

**Option A — Free Mockup**
"Let me show you what your new site could look like — for free."
Use Figma or a Next.js starter with their branding.

**Option B — Free Audit PDF**
Run `website_audit.py` → paste into a Canva 1-pager → send as PDF.

**Option C — PageSpeed Screenshot**
Run target URL on pagespeed.web.dev → screenshot red score → send:
"I can get this to green."

**Option D — Low-Cost Entry Project (₹3,000)**
"Let me fix just your mobile issue and SSL this week."
Often converts to a full rebuild once you deliver.

### Rapid Demo Strategy

Keep Vercel-deployed demo shells ready per category:
- `restaurant-demo.vercel.app`
- `clinic-demo.vercel.app`
- `boutique-demo.vercel.app`

Swap in their logo/content (20 min). Message: "Here's what yours could look like — tomorrow."

---

## PHASE 4 — WEEKLY WORKFLOW

### Daily Schedule (1.5 hours/day)

| Time | Task | Time |
|------|------|------|
| Morning | Run `lead_scraper.py` for today's batch | 5 min |
| Morning | Review CSV, pick top 10 leads | 10 min |
| Morning | Run `website_audit.py` on top 5 | 5 min |
| Morning | Send 5 WhatsApp/email outreach | 10 min |
| Evening | Reply to responses, book calls | 20 min |
| Evening | Update lead tracker (status) | 10 min |

### Weekly Rhythm

- **Monday** — Run full scraper (50 new leads). Rank them.
- **Tue–Thu** — 10 outreach messages/day (30 total).
- **Friday** — Follow-ups to Tue's no-replies. Client calls / demos.
- **Saturday** — Review metrics. Build this week's demo mockup.
- **Sunday** — Rest (or plan next week's category/area).

### Lead Tracker Columns (Google Sheets)

```
Name | Category | City | Phone | Website | Score | Priority
Date Contacted | Channel | Status | Notes | Follow-up Date
```

Status flow: `New → Contacted → Replied → Demo Sent → Call Booked → Closed Won / Lost`

---

## PRICING GUIDE

| Package | Included | Price |
|---------|----------|-------|
| Starter | 5 pages, mobile, contact form, SSL | ₹12,000–15,000 |
| Business | 8–10 pages + Contentful CMS + WhatsApp chat | ₹20,000–25,000 |
| E-commerce | Products, Razorpay checkout, order management | ₹35,000–45,000 |
| NGO | 6 pages, donation form, event section | ₹10,000–15,000 |
| Maintenance | Monthly updates, backups, uptime monitoring | ₹2,500–4,000/mo |

**Upsells after delivery:**
- Google Ads setup: ₹5,000 one-time
- Monthly SEO report: ₹2,000/mo
- WhatsApp Business automation: ₹3,000 one-time

---

## KPIs TO TRACK WEEKLY

| Metric | Target |
|--------|--------|
| New leads scraped | 50/week |
| Outreach sent | 30–40/week |
| Reply rate | 10–15% |
| Discovery calls booked | 2–3/week |
| Proposals sent | 1–2/week |
| Closes | 1–2/month |
| Monthly revenue | ₹30,000+ |

---

## MONTH 1 ACTION PLAN

### Week 1 — Setup
- [ ] Run `setup.bat` to install everything
- [ ] Edit `config.py` — set your name, phone, city
- [ ] Create Apollo.io + Hunter.io free accounts
- [ ] Set up Google Sheets lead tracker
- [ ] Create Calendly link for 30-min discovery calls
- [ ] Deploy one demo site per category on Vercel
- [ ] Run `lead_scraper.py` — get first 50 leads

### Week 2 — First Conversations
- [ ] Send 10 outreach messages (WhatsApp first)
- [ ] Follow up with Week 1 outreach
- [ ] Aim: 3 discovery calls booked
- [ ] Send audit + pitch to prospects who replied
- [ ] Goal: 1 closed client at ₹12,000+

### Week 3 — Scale
- [ ] Run scraper 3× (new categories/areas)
- [ ] 15–20 new outreach/day
- [ ] Start building Week 2 client's site
- [ ] Goal: 2nd client closed

### Week 4 — Hit the Target
- [ ] Deliver Week 2 client's site
- [ ] Sign 1 maintenance retainer
- [ ] 3rd client in pipeline
- [ ] Revenue check: aim ₹25,000+

---

## TOOLS STACK

### Free (Use Now)
- Playwright + BeautifulSoup — scraping + auditing
- Apollo.io — email finder (50/month free)
- Hunter.io — email verification
- Vercel — deploy demos free
- Canva — audit PDFs + mockups
- Google Sheets — lead CRM
- Calendly — book discovery calls

### Paid Upgrades (Once at ₹15k/month)
- PhantomBuster (~₹2,000/mo) — LinkedIn auto-connect + DM sequences
- Instantly.ai (~₹1,500/mo) — Email sequences with auto follow-up
- OpenAI API (~₹500/mo) — AI-personalised pitches at scale

---

## SCRIPTS QUICK REFERENCE

```bash
# Find hot leads in your city
python lead_scraper.py

# Audit a target's website + generate pitch (no API key needed)
python website_audit.py https://target.com "Business Name"

# Same, but with AI-powered pitch (needs OPENAI_API_KEY in .env)
python website_audit.py https://target.com "Business Name" --ai
```

---

*Next scripts to build together:*
1. Gmail API outreach script — auto-sends emails from leads.csv, zero copy-paste
2. WhatsApp blast tool — using Twilio or WA Business API
3. Auto-demo generator — deploys a live Vercel preview with client branding in 1 command
4. Google Sheets CRM sync — scraper auto-writes leads directly to Sheets
