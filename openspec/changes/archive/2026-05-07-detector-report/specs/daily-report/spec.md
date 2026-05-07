## ADDED Requirements

### Requirement: Daily count POST to webhook
The reporter script SHALL read today's break count from `counts.json` and POST a message to the configured webhook URL as `application/json` with body `{"text": "<message>"}`. The format SHALL be compatible with Slack incoming webhooks and any standard webhook receiver.

#### Scenario: Successful POST
- **WHEN** the reporter runs and the webhook URL is configured
- **THEN** an HTTP POST is sent with `Content-Type: application/json` and body `{"text": "<message>"}`

#### Scenario: Missing counts.json
- **WHEN** `counts.json` does not exist at report time
- **THEN** the reporter logs a warning and exits with code 0 (no webhook call made); a missing file means the daemon never wrote data today and sending a zero-count message would be misleading

#### Scenario: counts.json date is not today
- **WHEN** the stored date in `counts.json` differs from today (comparison uses `datetime.date.today()` in the system's configured local timezone, consistent with the daemon)
- **THEN** the reporter treats today's count as 0 and selects the zero message template

#### Scenario: Corrupt counts.json
- **WHEN** `counts.json` exists but contains malformed JSON, a non-dict top level, or a non-integer `today_count`
- **THEN** the reporter logs a warning, treats today's count as 0, and proceeds normally (exit 0, webhook call is still made with zero-count message); a corrupt file means the daemon ran and wrote something, so zero is a useful alert fallback

#### Scenario: Network or HTTP error
- **WHEN** the HTTP request fails (connection refused, DNS/TLS error, non-2xx response, or timeout after 10 s)
- **THEN** the reporter logs the error with HTTP status and up to 500 characters of response body (where available) and exits with code 1

### Requirement: Threshold-based message selection
The reporter SHALL select one of three message templates based on today's count relative to a configurable threshold (`detector_report_threshold`, default 2):

- count ≥ threshold → `detector_report_msg_ok`
- 0 < count < threshold → `detector_report_msg_low`
- count == 0 → `detector_report_msg_zero`

If the literal token `{count}` appears in a template it SHALL be replaced with the decimal representation of the count as a plain integer (no padding or fractional formatting) via `str.format(count=N)`. All occurrences are replaced if the token appears multiple times. Strings such as `{counter}` or `{{count}}` (Python escaped braces) SHALL NOT be treated as `{count}` and must not be replaced. The token is optional — templates that omit it send no count figure, which is the privacy-preserving default.

#### Scenario: Count at or above threshold
- **WHEN** today's count is greater than or equal to `detector_report_threshold`
- **THEN** `detector_report_msg_ok` is used as the message (with `{count}` replaced if present in the template)

#### Scenario: Count below threshold but nonzero
- **WHEN** today's count is greater than 0 and less than `detector_report_threshold`
- **THEN** `detector_report_msg_low` is used as the message (with `{count}` replaced if present in the template)

#### Scenario: Count is zero
- **WHEN** today's count is 0
- **THEN** `detector_report_msg_zero` is used as the message (with `{count}` replaced if present in the template)

### Requirement: Configurable message templates
The three message templates SHALL be configurable via Ansible variables with the following defaults:

- `detector_report_msg_ok`: `"Beam breaks today: ✅ OK (equal or above threshold)"`
- `detector_report_msg_low`: `"Beam breaks today: 🚨 under threshold"`
- `detector_report_msg_zero`: `"Beam breaks today: 0 ⚠️ no breaks today, sensor might be down."`

The defaults intentionally omit `{count}` to avoid exposing exact behavioral data in notifications. Users who want the raw count can add `{count}` to any template via an Ansible variable override.

A user MAY set `detector_report_msg_zero` to the same value as `detector_report_msg_low` to collapse the two warning cases.

#### Scenario: Custom message template
- **WHEN** `detector_report_msg_ok` is overridden to `"All good: {count} breaks"`
- **THEN** the sent message uses the override with `{count}` correctly replaced

### Requirement: Systemd timer fires daily at configurable time
The reporter SHALL be triggered by a systemd timer unit daily at a configurable wall-clock time (`detector_report_time`, default `17:00`). The timer SHALL use `Persistent=true` so a missed fire (e.g. Pi was off) is executed once on next boot.

#### Scenario: Timer fires at configured time
- **WHEN** the system clock reaches `detector_report_time`
- **THEN** `beam-detector-report.service` is started by systemd

#### Scenario: Missed fire on reboot
- **WHEN** the Pi reboots after having missed the scheduled report time
- **THEN** the timer fires once at boot to send the report

### Requirement: Webhook URL is vault-backed
The webhook URL SHALL be stored encrypted in `group_vars/all/vault.yml` as `vault_detector_report_webhook_url` and referenced in `vars.yml` as `detector_report_webhook_url`. If the URL is empty, the reporter SHALL log a warning and exit 0 without making a network call.

#### Scenario: Empty webhook URL
- **WHEN** `detector_report_webhook_url` is an empty string
- **THEN** the reporter exits with code 0 and logs a warning, no HTTP request is made
