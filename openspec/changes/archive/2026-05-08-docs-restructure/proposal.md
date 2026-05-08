## Why

The README is 284 lines and mixes project overview with deep hardware
reference detail. Supplementary docs (`NOTIFICATIONS.md`,
`DEVELOPMENT.md`) live at the root with no strong convention requiring
it, making the root noisier than necessary.

## What Changes

- Move `DEVELOPMENT.md` → `docs/development.md`
- Move `NOTIFICATIONS.md` → `docs/notifications.md`
- Extract Raspberry Pi hardware content from README into `docs/hardware-raspberry-pi.md`
  (parts list, wiring diagram reference, Pi Zero section)
- Extract ESP32 hardware content from README into `docs/hardware-esp32.md`
  (parts list, wiring diagram reference)
- Update all internal links in README, role READMEs, and specs

## Capabilities

### New Capabilities

- `docs-structure`: A `docs/` directory housing hardware guides and
  supplementary docs, linked from README

### Modified Capabilities

- `github-actions-ci`: The requirement that `DEVELOPMENT.md` documents
  CI now refers to `docs/development.md`

## Impact

- `README.md`: Hardware sections replaced with summaries linking to
  `docs/hardware-*.md`; existing links to `DEVELOPMENT.md` and
  `NOTIFICATIONS.md` updated
- `roles/*/README.md`: Any links to moved files updated
- `openspec/specs/github-actions-ci/spec.md`: Path reference updated
  via delta spec
