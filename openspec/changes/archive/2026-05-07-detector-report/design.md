## Context

`detector-core` writes `/var/lib/beam_detector/counts.json` with the structure `{"date": "YYYY-MM-DD", "today_count": N, "history": {...}}`. The reporter reads this file once, selects a message, and POSTs to a webhook. It is a one-shot script — no daemon, no long-running process.

The deployment runs on Raspberry Pi OS (Debian). Ansible already manages the `detector` role; the reporter extends the same role rather than introducing a new one.

## Goals / Non-Goals

**Goals:**
- Daily push of today's break count to a configurable webhook
- Threshold-based message selection with three distinct states (ok / low / zero), configurable via `detector_report_threshold` (default `2`)
- Slack-compatible POST format (works with any standard webhook receiver)
- Configurable send time via systemd timer
- Vault-backed webhook URL

**Non-Goals:**
- Retry on webhook failure (fire-and-forget; a missed day is acceptable)
- Historical summaries (today's count only)
- Multiple webhook destinations
- Authentication beyond the URL itself

## Decisions

### 1. stdlib `urllib.request` over `requests` / `urllib3`

`urllib.request` ships with Python 3 stdlib — no additional apt package. The reporter only needs one POST with a JSON body, which `urllib.request.urlopen` handles cleanly. Adding `python3-requests` for a single call is unnecessary weight.

`urlopen` is called with `timeout=10` to prevent an indefinite hang. HTTPS certificate verification is the Python 3 default and is not overridden. Network and HTTP errors (`urllib.error.URLError`, `urllib.error.HTTPError`) are caught, logged with status/detail, and the script exits 1 — a transient failure the operator can see in `systemctl status beam-detector-report`. "Fire-and-forget" (Decision 2, Risks section) refers to the absence of a retry loop, not to silent error dropping; the failure is always logged and reflected in the exit code.

### 2. One-shot systemd service + timer (not cron)

Consistent with the project's systemd-first approach. A `.timer` unit gives a persistent schedule that survives missed fires (via `Persistent=true`). A cron job would need `cron` installed; systemd is already present. The service unit is `Type=oneshot` — starts, runs, exits.

### 3. Extend `detector` role rather than new role

The reporter is tightly coupled to `detector-core` (reads its JSON, shares its variables). A separate role would duplicate variable definitions and create a dependency ordering problem in `site.yml`. Adding files/templates/tasks to the existing `detector` role keeps the concern co-located.

### 4. Message selection order: zero check before threshold check

The threshold is configurable via `detector_report_threshold` (Ansible variable, default `2`; integer ≥ 1). It is passed to the reporter as the `DETECTOR_REPORT_THRESHOLD` environment variable.

```
if count == 0       → msg_zero
elif count < threshold → msg_low
else                → msg_ok
```

Zero is a special health-alert case distinct from "low but non-zero". Checking zero first avoids needing `0 < count < threshold` arithmetic in the template.

### 5. `{count}` as opt-in interpolation token; omitted from defaults for privacy

Python `str.format(count=N)` is simple and readable. Users can add `{count}` anywhere in a template via Ansible variable override. The default templates deliberately omit it: the threshold-based categories (ok / low / zero) carry all operationally useful signal, and including the exact count in a push notification exposes precise behavioral data to wherever that notification lands (Slack, email, etc.). Opt-in beats opt-out here.

### 6. Timer fires at 17:00, `Persistent=true`

`Persistent=true` means if the Pi was off at 17:00, the timer fires once on next boot. This prevents silently missing a day's report due to a reboot or power cut.

## Risks / Trade-offs

- **Reporter runs as non-root** (`beam-detector-report` user, member of `detector` group) — reads `counts.json` via group read on `/var/lib/beam_detector/`; requires no write access; minimal privilege for a script that only reads one file and makes one outbound HTTP call
- **Webhook URL in vault** → if vault is misconfigured, deploy fails loudly (acceptable — better than silent skip)
- **Fire-and-forget POST** → network failures abort the report with no retry → Mitigation: errors (URLError, HTTPError) are caught, logged with status/detail, and the script exits 1; systemd records the failure in the unit status; `Restart=no` prevents retry storms
- **counts.json missing at report time** → reporter must handle gracefully (log warning, exit 0, no webhook call) — a missing file means the daemon never wrote data today; sending a zero-count message would be misleading. Not exit 1, which would generate a failed-unit alert.
- **counts.json corrupt at report time** → treat count as 0 and still POST the zero-count message (exit 0). Distinct from missing: a corrupt file means the daemon ran and wrote something; zero is a safe fallback that still delivers a useful alert.
- **Persistent=true on timer** → if Pi reboots repeatedly in one day, report fires multiple times → Mitigation: acceptable given low reboot frequency; a dedupe file could be added in a future increment if needed

## Migration Plan

1. Add `vault_detector_report_webhook_url` to `group_vars/all/vault.yml` (encrypted)
2. Add `detector_report_webhook_url` reference to `group_vars/all/vars.yml`
3. Run `ansible-playbook playbooks/site.yml` — role deploys reporter script, timer, service
4. Run `ansible-playbook playbooks/verify.yml` — asserts timer enabled
5. Rollback: `systemctl disable --now beam-detector-report.timer beam-detector-report.service`

## Open Questions

None.

## See Also

- `notes/implementation.md` — urllib.request POST snippet, message selection logic, counts.json read pattern, config passing strategy
