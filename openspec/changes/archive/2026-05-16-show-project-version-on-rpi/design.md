> See also: [notes/impl.md](notes/impl.md) — safe Ansible lookup syntax and placement

## Context

The ESPHome firmware already surfaces its version via `ESPHOME_PROJECT_VERSION`.
The RPi side (Flask web UI) shows no version, making it impossible to confirm at
a glance whether a deployment landed.

The project uses annotated git tags (`v2.2.1`, etc.) and a CHANGELOG. `git
describe` without `--tags` produces strings like `v2.2.1` (exact tag) or
`v2.2.1-3-g543b3e5` (3 commits ahead), which captures both release identity and
dirty-state distance.

The existing pattern in `beam-detector-web.service.j2` already injects runtime
config as `Environment=` lines (e.g. `DETECTOR_PICO_CSS`), so injecting
`DETECTOR_VERSION` follows the same seam.

## Goals / Non-Goals

**Goals:**

- Show the deployed project version in the Flask UI footer, baked in at Ansible
  run time
- No runtime git dependency on the Pi

**Non-Goals:**

- Live version polling or auto-refresh
- Showing version anywhere other than the footer

## Decisions

### Capture version on the control host, not the Pi

`git describe` runs on the Ansible control host via `lookup('pipe', 'git
describe')`. The resulting string is set as a fact (`detector_version`) and
injected into the systemd unit as `Environment=DETECTOR_VERSION=…`.

**Alternative considered**: a `VERSION` file checked into the repo. Rejected —
redundant source of truth that must be manually kept in sync with tags.

**Alternative considered**: `git describe` on the Pi at runtime. Rejected —
requires git on the Pi and the repo present there; adds unnecessary complexity.

### `git describe --tags`

`--tags` makes `git describe` resolve both annotated and lightweight tags. This
repo has a lightweight `initial` tag at the very first commit, so failure is
impossible. The output `v2.2.1-3-g543b3e5` conveys exact release or
distance-from-release, useful for diagnosing partial deploys.

### Render in footer next to GitHub link

Consistent with the ESPHome pattern of a read-only informational sensor. No interactivity needed.

## Risks / Trade-offs

- [Untagged repo state] Non-issue — `--tags` includes the lightweight `initial`
  tag present since the first commit, so `git describe --tags` always resolves.
- [Dirty working tree] `git describe` does not add a `-dirty` suffix by default.
  Acceptable — the commit hash is sufficient for diagnosis; exact dirtiness is a
  dev concern, not a deployment concern.

## Migration Plan

1. Add `detector_version` fact to role (or playbook) via `set_fact` + `lookup`
2. Add `Environment=DETECTOR_VERSION={{ detector_version }}` to
   `beam-detector-web.service.j2`
3. Add `DETECTOR_VERSION` env var read in `web.py` footer
4. Deploy via `ansible-playbook playbooks/site.yml`; no rollback needed (purely
   additive)
