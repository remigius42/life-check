## Context

`life-check.yaml` currently references non-secret user config via `!secret`
(pulling from `secrets.yaml`), conflating credentials with preferences.
ESPHome's `substitutions:` block provides pre-YAML-parse string replacement,
designed exactly for user-tunable defaults. The existing `on_time` trigger fires
at a hardcoded hour; making it runtime-configurable requires a different
approach since `on_time` triggers are compiled-in.

## Goals / Non-Goals

**Goals:**

- All non-secret user config lives in a single `substitutions:` block at the top
  of `life-check.yaml`
- Report time (hour + minute) is runtime-configurable via web UI without
  reflashing
- `secrets.yaml` contains only true credentials

**Non-Goals:**

- Making `beam_gpio_pin`, `beam_debounce`, or `timezone` runtime-configurable
  (compile-time is intentional for these)
- Changing any runtime behavior (debounce timing, retry logic, etc.)

## Decisions

**`substitutions:` over YAML anchors**: ESPHome supports dot-prefixed hidden
anchor blocks, but `substitutions:` is the idiomatic, supported mechanism with
clear documentation. Anchors cannot interpolate within strings and are less
readable.

**`beam_gpio_pin`, `beam_debounce`, `timezone` are compile-time only**: GPIO pin
is physically wired at assembly; exposing it in the web UI would be meaningless.
Debounce is a sensor-spec parameter (50–200 ms spec), not a user preference —
misconfiguration is silent and harmful. Timezone uses opaque POSIX strings
(e.g., `CET-1CEST,M3.5.0,M10.5.0/3`); a free-text UI field is a foot-gun.

**Per-minute poll for report time**: ESPHome `on_time` triggers are compiled-in
and cannot reference runtime entities. The alternative — an hourly trigger
checking only the hour — would lose minute granularity. A per-minute trigger
with `lambda: t.hour == report_hour && t.minute == report_minute` is clean and
correct. Overhead is negligible (one lambda call per minute).

**Two separate `number:` entities for hour and minute**: ESPHome has no native
time-of-day entity type. Two `number:` entities with clear labels and value
ranges (0–23, 0–59) are the idiomatic solution.

**Message templates move to `substitutions:`, not a second secrets file**: They
are user preferences, not credentials. Keeping them in `secrets.yaml` was a
workaround; `substitutions:` is the correct home. Default values are aligned
with `roles/detector/defaults/main.yml`.

**`web_server_version` is compile-time only**: The web server version is set in the
`substitutions:` block and baked into the firmware at compile time. It cannot be changed
via the web UI or NVS. v2 is the default because v3 causes significant UI latency and HTTP
server task contention on WROOM hardware. v3 is an opt-in upgrade for S3 boards or when
sorting groups, sensor graphs, or browser-OTA UI are needed — requires uncommenting the
`sorting_groups` block and per-entity `web_server:` blocks.

**`project.version` is compile-time only**: Exposed via the `ESPHOME_PROJECT_VERSION` C++
macro, which is substituted at compile time from the `esphome.project.version` field in
`life-check.yaml`. It cannot be changed at runtime. Must be updated manually before tagging
a release.

**`local: true` on web_server**: Assets are served from device flash rather than a CDN.
This ensures the web UI works on isolated home networks with no internet access — the primary
deployment environment for this system.

**`ota: platform: web_server`**: Enables firmware upload via the device web UI without the
ESPHome CLI. Useful for handing off a compiled `.bin` to a non-technical deployer.

**`Reset to Defaults (not webhook URL)` button**: Restores all NVS-persisted entities
(thresholds, retries, report time, message templates) to their substitution-block defaults.
The webhook URL is explicitly excluded because it contains an auth token — accidentally
resetting it would silently break daily reports.

## Risks / Trade-offs

- **Per-minute trigger fires 1440×/day** vs 1×/day previously → negligible on
  ESP32; lambda is a single integer comparison
- **`report_hour`/`report_minute` initial values are baked into
  firmware** → if user changes them via web UI, reflashing resets to
  substitution defaults (same behavior as `break_threshold` and
  `webhook_retries` today, which users already accept)

## Migration Plan

**Before flashing:**

1. Open `esphome/life-check.yaml` and update the `substitutions:` block:
   - Set `beam_gpio_pin` if your wiring differs from the default (GPIO13)
   - Set `timezone` if you are not in `Europe/Zurich`
   - Optionally update the message templates if you want different defaults on a clean flash

2. Remove the following keys from your local `secrets.yaml` (no longer referenced;
   ESPHome emits a parse warning for each unknown key):
   `timezone`, `beam_gpio_pin`, `msg_ok`, `msg_low`, `msg_zero`

**NVS-persisted values (webhook URL, messages, threshold, retries, report time):**
These entities use `restore_value: true`. Values already stored in NVS from a previous
flash are preserved — the `initial_value` from `substitutions:` only applies on first
boot when no NVS entry exists. No action needed if the device has been running.

**Note on message defaults:** The default message text has changed to align with
`roles/detector/defaults/main.yml`. Existing deployers with NVS-stored messages are
unaffected. New deployers or those who clear NVS will get the new defaults.

**Rollback:** Revert `life-check.yaml` and `secrets.yaml` to the prior state and
re-flash. NVS values are unaffected by rollback.
