<!-- spellchecker: ignore integromat -->

# Notifications

The system sends one HTTP POST per day (17:00 by default) to a configurable
webhook URL. Any service that can receive a POST request and trigger a
notification works. This document covers the most common options.

## Slack (recommended)

Slack incoming webhooks are the simplest setup and work on all Slack plans.

### 1. Create the webhook

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create a new app
   (or open an existing one).
1. Under **Features → Incoming Webhooks**, toggle the feature on.
1. Click **Add New Webhook to Workspace**, pick a channel, and authorize.
1. Copy the generated URL (`https://hooks.slack.com/services/…`).

### 2. Configure the project

**Raspberry Pi route** — add the URL to your vault:

```yaml
# group_vars/all/vault.yml
vault_webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

**ESPHome route** — add it to `esphome/secrets.yaml`:

```yaml
webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

The payload the system sends is a plain JSON object with a `text` field, which
Slack renders as a message in the chosen channel.

Message templates support a `{count}` placeholder for today's crossing count. The
default templates omit it intentionally — including exact numbers in a shared channel
could reveal more about someone's daily routine than intended.

______________________________________________________________________

## Alternatives

All alternatives below have a free tier sufficient for one POST per day (~30
notifications/month).

### Email via Make (formerly Integromat)

[Make](https://make.com) can receive a webhook and forward it as an email.
Free tier: 1,000 operations/month (a 2-step scenario costs 2 ops per run →
~500 runs/month).

1. Sign up at [make.com](https://make.com) (free).
1. Create a new **Scenario**.
1. Add a **Webhooks → Custom webhook** module as the trigger. Make gives you a
   unique HTTPS URL to POST to.
1. Add a **Gmail** (or **Email → Send an email**) module as the action.
   Configure recipient, subject, and body. Use the webhook payload fields for
   the message body.
1. Activate the scenario.
1. Set `vault_webhook_url` / `webhook_url` to the Make webhook URL.

### Telegram via Make

Same Make scenario setup as above, but replace the email module with
**Telegram Bot → Send a message**.

1. Create a Telegram bot via [@BotFather](https://t.me/BotFather) and note the
   bot token.
1. Start a conversation with the bot (or add it to a group) to get the chat ID.
1. In the Make scenario, add a **Telegram Bot → Send a message** module with
   the token and chat ID.

### Telegram bot (direct, no Make)

For a leaner setup without Make, use the Telegram Bot API directly. The system
posts to any HTTP URL, so you can use Telegram's `sendMessage` endpoint as the
webhook URL:

```text
https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<CHAT_ID>&text=
```

This requires the payload to match Telegram's query-parameter format. Because
the system sends a JSON body, you either need a thin proxy (e.g. a free
Cloudflare Worker or Pipedream workflow) or the Make route above.

### Pipedream

[Pipedream](https://pipedream.com) is a developer-friendly alternative to Make.
Free tier: ~100 workflow executions/day.

1. Sign up and create a new **Workflow**.
1. Use **HTTP / Webhook** as the trigger.
1. Add a **Send Email** or **Telegram** action.
1. Deploy the workflow and copy the trigger URL.
1. Set `vault_webhook_url` / `webhook_url` to that URL.

______________________________________________________________________

## Testing the webhook

Send a test POST manually to verify the pipeline before deploying:

```bash
curl -X POST <your-webhook-url> \
  -H "Content-Type: application/json" \
  -d '{"text": "test notification from life-check"}'
```

A `2xx` response means the endpoint accepted the request.
