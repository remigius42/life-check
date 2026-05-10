# [Life Check](https://github.com/remigius42/life-check)

Copyright 2026 [Andreas Remigius Schmidt](https://github.com/remigius42)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%20OS%20Bookworm-lightgrey.svg)
[![CI](https://github.com/remigius42/life-check/actions/workflows/ci.yml/badge.svg)](https://github.com/remigius42/life-check/actions/workflows/ci.yml)

An unobtrusive life-check system for elderly people — a positive take on the
[dead man's switch](https://en.wikipedia.org/wiki/Dead_man%27s_switch) concept.

A break-beam sensor mounted in a doorway counts daily crossings. A daily webhook
report flags when the count is unusually low, giving family or caregivers a quiet
signal without cameras, wearables, or any required action from the person being
monitored.

## What it does

- Counts daily break-beam crossings via a doorway sensor
- Sends a daily webhook report with a configurable low-count alert
- Exposes a responsive **"Life Check" web UI** with live status (SSE), 14-day
  history, test mode, and manual reset capability

## Deployment routes

Both routes use the same DFRobot sensor and deliver the same core features.

| Route               | Pros                                                                                        | Cons                                                                                          |
| ------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| **Raspberry Pi**    | Familiar Linux environment; easy to add future automations; history persists across reboots | Heavier setup (Ansible, Python stack, systemd); higher power draw; more expensive             |
| **ESP32 + ESPHome** | Simpler setup (flash one firmware); lower power; cheaper hardware; built-in web UI and OTA  | 14-day history resets on reboot (today's count is preserved); customization requires YAML/C++ |

Pick your route for the full guide:

- [Raspberry Pi route](docs/raspberry-pi.md) — parts, wiring, Ansible setup
- [ESP32 route](docs/esp32.md) — parts, wiring, ESPHome setup

## License

MIT — see individual role READMEs for per-role attribution.

[Pico CSS](https://picocss.com) (Copyright 2019-2025) is vendored under the MIT license.
The license notice is preserved in `roles/detector/files/static/pico-*.min.css`.

## Development

See [docs/development.md](docs/development.md) for local setup, running tests, linting,
and the change workflow.

See [docs/notifications.md](docs/notifications.md) for webhook setup (Slack, email, Telegram).

## Contributing

PRs are welcome. Fair warning: this is a personal project maintained on a
best-effort basis, so responses and reviews may be slow and changes that don't
fit the use case are unlikely to be merged.
[Opening an issue first to discuss](https://github.com/remigius42/life-check/issues/new?template=feature_request.yml)
is the best use of your time.

Please note that this project is released with a
[Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating
you agree to abide by its terms.
