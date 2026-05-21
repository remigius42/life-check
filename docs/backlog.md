# Backlog

<!-- spellchecker:ignore wokwi -->

Tracked future work and explored-but-parked ideas.

For active exploration of a specific idea, open an OpenSpec change under
[`openspec/changes/`](../openspec/changes/)`<name>/` (see
[development.md](development.md) for the workflow). A `purpose.md` artifact is a
good lightweight commitment — it captures the problem statement without locking
in any design decisions.

Personal short-term notes live in `/TODO.md` (gitignored scratchpad, not tracked
here).

## Parked

Ideas worth revisiting if circumstances change, but not worth the setup cost
now.

### ESP32 firmware simulation with Wokwi CI

Run ESPHome-compiled firmware in [Wokwi](https://wokwi.com) as part of CI using
[pytest-embedded-wokwi](https://docs.espressif.com/projects/pytest-embedded/en/latest/apis/pytest-embedded-wokwi.html)
or the [Wokwi CI GitHub Action](https://docs.wokwi.com/wokwi-ci/github-actions).

**Why parked:**

- ESPHome's own test suite already covers the framework; the firmware logic we
  add on top is comparatively small.
- Pre-commit hooks validate the YAML before anything reaches CI.
- The YAML has been validated on real TTGO hardware and worked correctly.
- The setup cost is non-trivial: `diagram.json` (virtual wiring), `wokwi.toml`,
  serial log assertions, a CI token, and ongoing paid simulation minutes beyond
  the free tier (50 min/month).
- With a low firmware change rate, the marginal quality gain does not justify
  the maintenance overhead.

**Revisit if:** firmware complexity grows significantly (more scripts, more
edge-case logic) or the change rate increases to the point where regressions
become a real risk.

## Rejected

Ideas that were considered and dismissed. Listed here so they are not
re-proposed without new information.

### MicroPython route for ESP32

A third deployment route using MicroPython instead of ESPHome.

**Why rejected:**

- Three routes is not sustainable for a personal project maintained on a
  best-effort basis.
- MicroPython fills no gap in the existing spectrum: Raspberry Pi covers
  flexibility (Linux, Python, Ansible); ESPHome covers low friction (YAML,
  flash and done). MicroPython sits between the two — more work than ESPHome,
  less flexible than RPi.
- HA integration is weaker: ESPHome's native API is impossible on MicroPython
  (protobuf overhead); the alternative is MQTT with auto-discovery, which works
  but is a different integration model and requires more setup.
- OTA requires manual implementation in MicroPython (partition management,
  custom server); ESPHome's is baked in. NVS and SNTP are native in both.
