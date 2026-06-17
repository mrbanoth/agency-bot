import sys, time
from dotenv import load_dotenv

load_dotenv()

# Configure stdout/stderr encoding
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"): sys.stderr.reconfigure(encoding="utf-8")

import telegram_notifier
import reply_checker

# GitHub Actions schedules fire every ~5 min at best, with extra jitter
# under load. Instead of checking once and exiting, stay alive and poll
# Telegram every few seconds for most of that window — this turns a
# "once every 30 min" bot into a "near real-time" one, for free.
ACTIVE_WINDOW_SECONDS  = 4.5 * 60   # leave headroom inside the 5-min cron gap
TELEGRAM_POLL_SECONDS  = 3
EMAIL_CHECK_SECONDS    = 60         # IMAP login is slower — don't hammer it


def main():
    print("====================================================")
    print("      AGENCY BOT — CHECK COMMANDS & REPLIES         ")
    print("====================================================")

    start = time.time()
    last_email_check = 0.0
    loops = 0

    while time.time() - start < ACTIVE_WINDOW_SECONDS:
        loops += 1
        try:
            telegram_notifier.handle_commands()
        except Exception as e:
            print(f"  [Telegram] poll error: {e}")

        if time.time() - last_email_check >= EMAIL_CHECK_SECONDS:
            try:
                reply_checker.check_replies()
            except Exception as e:
                print(f"  [Replies] check error: {e}")
            last_email_check = time.time()

        time.sleep(TELEGRAM_POLL_SECONDS)

    print(f"\n====================================================")
    print(f"Check loop finished — {loops} Telegram polls over {ACTIVE_WINDOW_SECONDS/60:.1f} min.")

if __name__ == "__main__":
    main()
