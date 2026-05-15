# Implementation reference

## Value mapping

Every value being moved, with source → destination and current/default value.

| Key | From | To | Value |
|---|---|---|---|
| `beam_gpio_pin` | `secrets.yaml` (`!secret`) | `substitutions:` | `GPIO13` |
| `timezone` | `secrets.yaml` (`!secret`) | `substitutions:` | `"Europe/Zurich"` |
| `msg_ok` | `secrets.yaml` (`!secret`) | `substitutions:` | `"Beam breaks today: ✅ OK (equal or above threshold)"` |
| `msg_low` | `secrets.yaml` (`!secret`) | `substitutions:` | `"Beam breaks today: 🚨 under threshold"` |
| `msg_zero` | `secrets.yaml` (`!secret`) | `substitutions:` | `"Beam breaks today: 0 ⚠️ no breaks today, sensor might be down."` |
| `notification_hour` | hardcoded `hours: 17` | `substitutions:` | `"17"` |
| `notification_minute` | (did not exist) | `substitutions:` | `"0"` |
| `test_mode_timeout` | hardcoded `delay: 30min` | `substitutions:` | `30min` |
| `http_timeout` | hardcoded `timeout: 10s` | `substitutions:` | `10s` |
| `break_threshold` | `initial_value: 2` | `substitutions:` | `"2"` |
| `webhook_retries` | `initial_value: 3` | `substitutions:` | `"3"` |
| `beam_debounce` | hardcoded `100ms` (×2) | `substitutions:` | `100ms` |

Message defaults sourced from `roles/detector/defaults/main.yml` lines 23–25.

Keys removed from `secrets.yaml.example`: `timezone`, `beam_gpio_pin`, `msg_ok`, `msg_low`, `msg_zero`

## Per-minute report trigger (replaces `hours: 17`)

```yaml
      - seconds: 0
        minutes: /1
        then:
          - if:
              condition:
                lambda: |-
                  auto t = id(sntp_time).now();
                  return t.hour == (int)id(report_hour).state
                      && t.minute == (int)id(report_minute).state;
              then:
                - script.execute: send_daily_report
```

## New number entities (add after existing `webhook_retries` entity)

```yaml
  - platform: template
    id: report_hour
    name: "Report Hour"
    min_value: 0
    max_value: 23
    step: 1
    restore_value: true
    optimistic: true
    initial_value: $notification_hour
  - platform: template
    id: report_minute
    name: "Report Minute"
    min_value: 0
    max_value: 59
    step: 1
    restore_value: true
    optimistic: true
    initial_value: $notification_minute
```

## docs/esp32.md touch points

- Line 25: `beam_gpio_pin` reference in wiring section — update to say `substitutions:` block
- Line 34: TTGO section mentions `beam_gpio_pin` in `secrets.yaml` — update
- Lines 84–87: Step 2 "Create your secrets file" — rewrite to explain two-file split and what can be deferred to web UI
- Lines 111–120: Step 5 "Configure webhook and thresholds" — add `{count}` token note
