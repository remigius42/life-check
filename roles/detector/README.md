<!-- spellchecker: ignore raspi usermod -->

# Detector

Installs and manages the `beam-detector` daemon and daily reporter. The daemon is a Python polling
service that detects break-beam events on a Raspberry Pi GPIO pin, maintains a daily break counter,
and persists history to JSON. The reporter reads the persisted counts and sends a daily webhook report.

## Requirements

- Raspberry Pi OS (Debian-based); tested on Raspberry Pi OS Bookworm
- Ansible 2.14+
- `python3-rpi.gpio` apt package (installed by this role)
- Hardware: break-beam sensor wired to GPIO pin 17 (BCM), open-collector receiver, pull-up required

## Dependencies

None.

## Role Variables

| Variable                            | Default                               | Description                                                          |
| ----------------------------------- | ------------------------------------- | -------------------------------------------------------------------- |
| `detector_gpio_pin`                 | `17`                                  | BCM GPIO pin number                                                  |
| `detector_poll_interval_ms`         | `50`                                  | Polling interval in milliseconds                                     |
| `detector_gpio_init_retries`        | `3`                                   | GPIO init retry attempts before fatal exit                           |
| `detector_history_retention_days`   | `14`                                  | Days of break-count history to retain                                |
| `detector_test_mode_grace_period_s` | `1800`                                | Seconds before test mode auto-reverts (30 min)                       |
| `detector_install_dir`              | `/opt/beam_detector`                  | Directory for the daemon script                                      |
| `detector_config_dir`               | `/etc/beam_detector`                  | Directory for `config.ini`                                           |
| `detector_data_dir`                 | `/var/lib/beam_detector`              | Persistent storage for `counts.json`                                 |
| `detector_run_dir`                  | `/run/beam_detector`                  | tmpfs runtime dir (managed by systemd `RuntimeDirectory`)            |
| `detector_counts_path`              | `{{ detector_data_dir }}/counts.json` | Daily break-count history file                                       |
| `detector_state_path`               | `{{ detector_run_dir }}/state.json`   | Live state IPC file (written every poll tick)                        |
| `detector_test_mode_sentinel`       | `{{ detector_run_dir }}/test_mode`    | Sentinel file that activates test mode                               |
| `detector_service_user`             | `root`                                | OS user that runs the service (see note below)                       |
| `detector_group`                    | `detector`                            | System group for IPC — daemon and reporter run in this group         |
| `detector_report_user`              | `beam-detector-report`                | OS user that runs the reporter oneshot service                       |
| `detector_report_webhook_url`       | `""`                                  | Slack/webhook URL; if empty reporter exits 0 without posting         |
| `detector_report_time`              | `"17:00"`                             | Daily timer schedule (`OnCalendar` value)                            |
| `detector_report_threshold`         | `2`                                   | Break count below which `msg_low` is sent instead of `msg_ok`        |
| `detector_report_msg_ok`            | *(see defaults)*                      | Message when count ≥ threshold; `{count}` opt-in token available     |
| `detector_report_msg_low`           | *(see defaults)*                      | Message when 0 < count < threshold; `{count}` opt-in token available |
| `detector_report_msg_zero`          | *(see defaults)*                      | Message when count == 0; `{count}` opt-in token available            |

## Service User

On modern Raspberry Pi OS (Bookworm+) GPIO access is granted via the `gpio` group; running as
`root` is not required. The recommended setup:

```bash
useradd -r -s /usr/sbin/nologin beam_detector
usermod -aG gpio beam_detector
```

Then set `detector_service_user: beam_detector` in your playbook vars. The default remains
`root` for backwards compatibility with older OS images that lack the `gpio` group.

## Example Playbook

```yaml
- hosts: raspi
  roles:
    - role: detector
      vars:
        detector_gpio_pin: 17
        detector_history_retention_days: 30
        detector_test_mode_grace_period_s: 600
```

## License

MIT
