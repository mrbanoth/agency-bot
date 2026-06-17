"""
webhook_handler.py — Instant Telegram command entrypoint.

Triggered by .github/workflows/telegram_webhook.yml on a `repository_dispatch`
event (type: telegram_message), fired by the Cloudflare Worker the instant
Telegram delivers a message — no polling, no 5-minute cron wait.

The Worker forwards the raw Telegram `update` JSON as the event's
client_payload. GitHub exposes that payload to this script via the
GITHUB_EVENT_PATH file (standard Actions behavior), so we read it from there
instead of needing a separate env var.
"""
import sys, os, json
from dotenv import load_dotenv

load_dotenv()

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"): sys.stderr.reconfigure(encoding="utf-8")

import telegram_notifier


def main():
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if not event_path or not os.path.exists(event_path):
        print("  [Webhook] No GITHUB_EVENT_PATH found — nothing to process.")
        return

    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    update = event.get("client_payload", {}).get("update")
    if not update:
        print("  [Webhook] No update in client_payload — nothing to process.")
        return

    handled = telegram_notifier.process_update(update)
    print(f"  [Webhook] Update processed: {handled}")


if __name__ == "__main__":
    main()
