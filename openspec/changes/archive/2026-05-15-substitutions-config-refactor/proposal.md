## Why

Configuration values are scattered between hardcoded YAML and `secrets.yaml`,
making first-time setup harder than necessary and blurring the line between
credentials and user preferences. ESPHome's `substitutions:` block is the
idiomatic solution: a single, self-documenting section at the top of the config
file for all non-secret user-tunable parameters.

## What Changes

- Add a `substitutions:` block to `life-check.yaml` containing all non-secret
  user-tunable values: `beam_gpio_pin`, `beam_debounce`, `timezone`,
  `notification_hour`, `notification_minute`, `test_mode_timeout`,
  `http_timeout`, `break_threshold`, `webhook_retries`, and the three message
  templates
- Add `report_hour` and `report_minute` `number:` entities (runtime-configurable
  via web UI, NVS-persisted, initial values from substitutions)
- Replace the static `on_time: hours: 17` trigger with a per-minute poll that
  compares current time against the `report_hour`/`report_minute` entities
- Remove non-secret keys from `secrets.yaml.example` (`timezone`,
  `beam_gpio_pin`, `msg_ok`, `msg_low`, `msg_zero`); retain only true
  credentials
- Update `docs/esp32.md`: clarify the two-file config split, explain what must
  be set before flashing vs. what can be deferred to the web UI, and document
  the `{count}` message template token

## Capabilities

### New Capabilities

_(none — this is a configuration refactor)_

### Modified Capabilities

- `esphome-firmware`: Initial values for runtime-configurable entities move from
  `secrets.yaml` to `substitutions:`; report time becomes runtime-configurable
  (hour + minute) instead of hardcoded at 17:00; `beam_gpio_pin` and `timezone`
  move from `secrets.yaml` to `substitutions:` (compile-time, not exposed in web
  UI)

## Impact

- `esphome/life-check.yaml` — significant restructuring
- `esphome/secrets.yaml.example` — 5 keys removed
- `docs/esp32.md` — setup instructions updated
