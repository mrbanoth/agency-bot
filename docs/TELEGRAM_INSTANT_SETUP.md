# Instant Telegram Commands — Setup (one-time, ~10 minutes, 100% free)

Right now the bot checks Telegram every ~5 minutes (GitHub Actions cron limit).
This setup makes commands like `/pipeline`, `/note`, `/close` respond in
**1-3 seconds**, using a free Cloudflare Worker as an instant relay between
Telegram and GitHub Actions.

No credit card required for any step.

## How it works

```
Telegram message → Cloudflare Worker → GitHub repository_dispatch
                                       → telegram_webhook.yml runs instantly
                                       → webhook_handler.py replies
```

## Step 1 — Create a GitHub fine-grained PAT

1. Go to https://github.com/settings/personal-access-tokens/new
2. Token name: `agency-bot-webhook-relay`
3. Resource owner: your account. Repository access: **Only select repositories** → `mrbanoth/agency-bot`
4. Permissions → Repository permissions → **Actions: Read and write**
5. Generate token, copy it (starts with `github_pat_...`). You won't see it again.

## Step 2 — Create the Cloudflare Worker

1. Go to https://dash.cloudflare.com → sign up free (no card needed) → **Workers & Pages**
2. **Create application → Create Worker** → name it `agency-bot-relay` → Deploy (deploys a placeholder first)
3. Click **Edit code**, delete everything, paste in the full contents of `cloudflare_worker.js` from this repo, click **Deploy**.
4. Go to the Worker's **Settings → Variables and Secrets** → add 3 **secret** variables:
   - `GH_PAT` = the PAT from Step 1
   - `GH_REPO` = `mrbanoth/agency-bot`
   - `TELEGRAM_WEBHOOK_SECRET` = any random string you make up (e.g. `a1b2c3-pick-your-own-d4e5f6`)
5. Save. Note your Worker's URL, shown at the top of the Worker page — looks like:
   `https://agency-bot-relay.<your-subdomain>.workers.dev`

## Step 3 — Point Telegram at the Worker

Run this once from any terminal (replace the placeholders), using the same
secret you set in Step 2 and your real bot token:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://agency-bot-relay.<your-subdomain>.workers.dev",
    "secret_token": "<TELEGRAM_WEBHOOK_SECRET you chose>"
  }'
```

A `{"ok":true,...}` response means it's live. From now on, every Telegram
message you send is relayed instantly — no more waiting for the 5-minute cron.

## Reverting (if you ever want to go back to polling-only)

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook"
```

After this, `getUpdates`-based polling (`check_replies.yml` /
`check_updates.py`) resumes working immediately — the two methods are
mutually exclusive, so only use one at a time.

## Notes

- While the webhook is active, the existing 5-minute polling job
  (`check_replies.yml` → `check_updates.py` → `telegram_notifier.handle_commands`)
  will log a harmless `Conflict` error on its Telegram polling step and
  continue on to its email-reply-check duties — no action needed, it's
  already wrapped in a try/except.
- The webhook path and the polling path both end up calling the same
  `telegram_notifier.process_update()` function, so every command behaves
  identically either way.
