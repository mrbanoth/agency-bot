/**
 * Agency Bot — Instant Telegram Relay (Cloudflare Worker, free tier)
 *
 * Telegram calls this Worker the instant a message arrives (webhook push).
 * The Worker immediately fires a GitHub `repository_dispatch` event carrying
 * the raw Telegram update, then returns 200 OK to Telegram right away.
 * GitHub Actions picks it up in ~5-10 seconds — no polling, no cron wait.
 *
 * Deploy: paste this whole file into a new Cloudflare Worker (dash.cloudflare.com
 * → Workers & Pages → Create → Edit code), then set these three Worker secrets
 * (Settings → Variables → Encrypt):
 *   GH_PAT                    - fine-grained GitHub PAT, repo-scoped, Actions: Read+Write
 *   GH_REPO                   - "mrbanoth/agency-bot"
 *   TELEGRAM_WEBHOOK_SECRET   - any random string you choose (also passed to setWebhook)
 *
 * See docs/TELEGRAM_INSTANT_SETUP.md for the full step-by-step.
 */

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("OK", { status: 200 });
    }

    // Verify the request actually came from Telegram, not a random caller.
    const secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token");
    if (secret !== env.TELEGRAM_WEBHOOK_SECRET) {
      return new Response("Forbidden", { status: 403 });
    }

    let update;
    try {
      update = await request.json();
    } catch (e) {
      return new Response("Bad Request", { status: 400 });
    }

    const dispatchUrl = `https://api.github.com/repos/${env.GH_REPO}/dispatches`;
    await fetch(dispatchUrl, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.GH_PAT}`,
        "Accept": "application/vnd.github+json",
        "User-Agent": "agency-bot-telegram-relay",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        event_type: "telegram_message",
        client_payload: { update },
      }),
    });

    // Always return 200 fast so Telegram doesn't retry-storm us.
    return new Response("OK", { status: 200 });
  },
};
