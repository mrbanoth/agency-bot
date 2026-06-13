"""
scheduler.py — Runs the full pipeline every day at the time set in config.py.
Keep this running in the background and it handles everything automatically.

START:  python scheduler.py
STOP:   Ctrl+C
"""

import sys, time, schedule, traceback
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from config import DAILY_RUN_TIME, LOG_FILE
from main import run, log


def safe_run():
    try:
        run()
    except Exception:
        err = traceback.format_exc()
        log(f"[Scheduler] Crash: {err}")


def main():
    log(f"[Scheduler] Started — will run daily at {DAILY_RUN_TIME}")
    log(f"[Scheduler] Keep this window open. Press Ctrl+C to stop.")

    schedule.every().day.at(DAILY_RUN_TIME).do(safe_run)

    # Also run immediately on first start so you see results right away
    log("[Scheduler] Running first cycle now ...")
    safe_run()

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
