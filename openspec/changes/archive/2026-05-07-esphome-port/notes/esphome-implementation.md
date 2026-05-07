<!-- spellchecker: ignore npos -->

# ESPHome Implementation Notes

## NVS / restore_value gotchas

**String length limit**: ESPHome's default NVS string storage is 63 chars. The Slack webhook URL is ~88 chars (`https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`), so every `text` entity needs `max_restore_data_length: 254` explicitly set.

**NVS exhaustion bug (ESPHome 2026.2.0)**: Accumulating many NVS-persisted values can exhaust the NVS partition. Keep NVS use to the 6 configured entities (4 `text` + 2 `number`) and use `restore_value: false` for all RAM globals.

## C++ array globals

ESPHome `globals` supports scalar types natively. For the 14-element history array, use a custom C++ global via `esphome/components/globals/globals_component.h` isn't needed — just declare it in a lambda's global scope using `esphome`'s custom `global_variable` or, simpler, use an `esphome` `globals` component with type `int[14]`:

```yaml
globals:
  - id: today_count
    type: int
    restore_value: false
    initial_value: '0'
  - id: daily_counts
    type: int[14]
    restore_value: false
    initial_value: '{0,0,0,0,0,0,0,0,0,0,0,0,0,0}'
  - id: test_mode_active
    type: bool
    restore_value: false
    initial_value: 'false'
```

ESPHome supports fixed-size array types in `globals`. The `initial_value` must be a valid C++ initializer string.

## FIFO shift on day rollover

On midnight, shift history array and reset today's count:

```yaml
time:
  - platform: sntp
    id: sntp_time
    timezone: ${timezone}
    on_time:
      - seconds: 0
        minutes: 0
        hours: 0
        then:
          - lambda: |-
              for (int i = 13; i > 0; i--) {
                id(daily_counts)[i] = id(daily_counts)[i-1];
              }
              id(daily_counts)[0] = id(today_count);
              id(today_count) = 0;
```

Index 0 = yesterday, index 1 = two days ago, ..., index 13 = 14 days ago.

## Webhook retry loop

ESPHome `http_request` returns a response object. Use a script with a loop variable to implement retry:

```yaml
script:
  - id: send_webhook
    parameters:
      message: string
    then:
      - lambda: |-
          int attempts = 0;
          int max_retries = (int) id(webhook_retries).state;
          bool success = false;
          while (attempts <= max_retries && !success) {
            // http_request must be called via action, not lambda
            // Use a globals flag instead — see pattern below
          }
```

**Note**: `http_request.post` is an ESPHome action, not callable from a C++ lambda directly. The cleanest approach is a recursive script or a counter global + interval check. Recommended pattern:

```yaml
globals:
  - id: webhook_attempt
    type: int
    restore_value: false
    initial_value: '0'

script:
  - id: do_webhook_attempt
    then:
      - http_request.post:
          url: !lambda 'return id(webhook_url).state;'
          headers:
            Content-Type: application/json
          body: !lambda |
            // build body string
            return "{\"text\": \"...\"}";
          on_response:
            then:
              - if:
                  condition:
                    lambda: 'return response->status_code >= 200 && response->status_code < 300;'
                  else:
                    - lambda: 'id(webhook_attempt) += 1;'
                    - if:
                        condition:
                          lambda: 'return id(webhook_attempt) <= (int)id(webhook_retries).state;'
                        then:
                          - delay: 30s
                          - script.execute: do_webhook_attempt

  - id: send_daily_report
    then:
      - lambda: 'id(webhook_attempt) = 0;'
      - script.execute: do_webhook_attempt
```

Call `send_daily_report` from the 17:00 time trigger.

## Test mode switch with auto-revert

```yaml
switch:
  - platform: template
    name: "Test Mode"
    id: test_mode_switch
    restore_mode: ALWAYS_OFF   # equivalent to restore_value: false
    turn_on_action:
      - lambda: 'id(test_mode_active) = true;'
      - script.execute: test_mode_revert_timer
    turn_off_action:
      - lambda: 'id(test_mode_active) = false;'
      - script.stop: test_mode_revert_timer

script:
  - id: test_mode_revert_timer
    mode: restart   # restart timer if switch is toggled on again
    then:
      - delay: 30min
      - switch.turn_off: test_mode_switch
```

`mode: restart` ensures re-enabling test mode resets the 30-minute clock. `script.stop` in `turn_off_action` cancels the pending delay cleanly.

## 3-tier message selection

```yaml
- lambda: |-
    int count = id(today_count);
    int threshold = (int) id(break_threshold).state;
    std::string tmpl;
    if (count == 0) {
      tmpl = id(msg_zero).state;
    } else if (count < threshold) {
      tmpl = id(msg_low).state;
    } else {
      tmpl = id(msg_ok).state;
    }
    // replace {count}
    std::string count_str = std::to_string(count);
    size_t pos = tmpl.find("{count}");
    if (pos != std::string::npos) {
      tmpl.replace(pos, 7, count_str);
    }
    // store result for use in http_request body action
    id(webhook_message) = tmpl;
```

Requires an additional `std::string` global `webhook_message` to pass the message from the lambda to the `http_request` action. Add `#include <string>` is not needed — ESPHome includes it via Arduino/ESP-IDF headers.

## web_server authentication

```yaml
web_server:
  port: 80
  auth:
    username: !secret web_username
    password: !secret web_password
```

## OTA password

```yaml
ota:
  - platform: esphome
    password: !secret ota_password
```

## secrets.yaml keys summary

```yaml
wifi_ssid: "YourSSID"
wifi_password: "YourWiFiPassword"
ota_password: "choose-a-strong-password"
web_username: "admin"
web_password: "choose-a-strong-password"
timezone: "Europe/Zurich"          # POSIX tz string
beam_gpio_pin: GPIO4               # adjust per board
webhook_url: "https://hooks.slack.com/services/..."
msg_ok: "All good — {count} crossings today."
msg_low: "Low activity — only {count} crossing(s) today."
msg_zero: "No crossings detected today. Please check in."
break_threshold: "2"
webhook_retries: "3"
```
