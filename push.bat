@echo off
title Pushing to GitHub...

echo.
echo ============================================
echo   Pushing Agency Bot to GitHub
echo ============================================
echo.

git init
git config user.name "Sandeep Naik"
git config user.email "sandeepnaikb0@gmail.com"
git branch -M main
git remote remove origin 2>nul
git remote add origin https://github.com/mrbanoth/agency-bot.git

echo.
echo [Staging files...]
git add config.py
git add main.py
git add pitch_engine.py
git add notifier.py
git add scheduler.py
git add lead_scraper.py
git add website_audit.py
git add requirements.txt
git add setup.bat
git add run_24_7.bat
git add outreach_templates.md
git add MASTER_PLAN_30k_Agency.md
git add HOW_TO_START.md
git add DEPLOY_TO_GITHUB.md
git add .gitignore
git add .github\workflows\daily_run.yml

echo.
echo [Creating commit...]
git commit -m "feat: automated freelance lead generation system

- Google Maps scraper for Hyderabad businesses
- Website quality auditor (SSL, speed, mobile, SEO)
- Groq AI pitch generator (free tier)
- Gmail digest notifier to self
- Daily scheduler (9 AM IST)
- GitHub Actions workflow for 24/7 cloud execution"

echo.
echo [Pushing to GitHub...]
echo.
echo  NOTE: GitHub will ask for your username + password.
echo  For password — use a Personal Access Token, NOT your real password.
echo  Get one: github.com/settings/tokens -> Generate new token (classic)
echo  Scopes needed: check 'repo' only.
echo.
git push -u origin main

echo.
if errorlevel 1 (
    echo  ERROR: Push failed. Check your token and try again.
) else (
    echo  SUCCESS! Code is live at:
    echo  https://github.com/mrbanoth/agency-bot
    echo.
    echo  Next: go to repo Settings - Secrets and add:
    echo    GMAIL_ADDRESS
    echo    GMAIL_APP_PASSWORD
    echo    GROQ_API_KEY
)
echo.
pause
