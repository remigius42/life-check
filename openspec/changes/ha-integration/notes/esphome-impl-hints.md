# ESPHome Implementation Hints

See [specs/esphome-ha-status/spec.md](../specs/esphome-ha-status/spec.md) and
[design.md](../design.md).

## Binary sensor: use `publish_state()`, not a polling lambda

The `ha_status_sensor` must NOT use an `update_interval` lambda — that would
push state on a timer regardless of jitter. Instead, give it no automatic
updates and drive it exclusively via `publish_state()` from the jitter script
and the midnight reset.

```yaml
binary_sensor:
  - platform: template
    id: ha_status_sensor
    name: "HA Status"
```

(No `lambda:` and no `update_interval:` — template binary sensors without a
lambda are purely manually published.)

## Jitter script: delay lambda syntax

ESPHome's `delay` action accepts a `!lambda` returning milliseconds (unsigned):

```yaml
script:
  - id: publish_ha_status
    mode: single  # subsequent threshold crossings during jitter window are ignored
    then:
      - delay: !lambda 'return (900 + rand() % ${ha_jitter_max_add_s}) * 1000u;'
      - lambda: >
          id(ha_status_sensor).publish_state(
            id(today_count) >= (int)id(break_threshold).state);
```

## Midnight reset: publish immediately, do not cancel pending script

At midnight rollover, publish OFF immediately (no jitter — deterministic event).
Do not cancel the jitter script if it happens to be running; when it eventually
fires it will re-read `today_count` (now 0, below threshold) and publish OFF
again — harmless.

```yaml
# in the midnight automation / time trigger:
- lambda: 'id(ha_status_sensor).publish_state(false);'
```

## Trigger point

Fire `script.execute: publish_ha_status` inside the beam-break automation,
after incrementing `today_count`, only when the count exactly reaches threshold
(to avoid re-triggering on subsequent breaks):

```yaml
- if:
    condition:
      lambda: 'return id(today_count) == (int)id(break_threshold).state;'
    then:
      - script.execute: publish_ha_status
```
