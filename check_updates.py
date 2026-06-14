import sys
from dotenv import load_dotenv

load_dotenv()

# Configure stdout/stderr encoding
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"): sys.stderr.reconfigure(encoding="utf-8")

import telegram_notifier
import reply_checker

def main():
    print("====================================================")
    print("      AGENCY BOT — CHECK COMMANDS & REPLIES         ")
    print("====================================================")

    # 1. Handle incoming Telegram commands
    print("\n[Step 1] Checking Telegram commands...")
    telegram_notifier.handle_commands()

    # 2. Check client email replies
    print("\n[Step 2] Checking client email replies...")
    reply_checker.check_replies()

    print("\n====================================================")
    print("Check finished successfully.")

if __name__ == "__main__":
    main()
