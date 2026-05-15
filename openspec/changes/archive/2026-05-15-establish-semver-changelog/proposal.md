## Why

The project has no versioning or changelog. Without these, breaking changes (like the upcoming substitutions-config-refactor) are invisible to existing deployers. Establishing semver and a changelog now gives a clean baseline and the right infrastructure to communicate future breaking changes.

## What Changes

- Create `CHANGELOG.md` at the repo root following [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) format with semantic versioning
- Summarize all current functionality into a `[1.0.0]` entry covering both routes (ESP32/ESPHome and Raspberry Pi/Ansible)
- Tag HEAD as `v1.0.0`

## Capabilities

### New Capabilities

- `changelog`: The project SHALL maintain a `CHANGELOG.md` at the repo root following Keep a Changelog 1.1.0 format with semantic versioning (MAJOR.MINOR.PATCH). Every OpenSpec change applied to main SHALL include a changelog entry. Breaking changes SHALL increment MAJOR.

### Modified Capabilities

_(none)_

## Impact

- `CHANGELOG.md` — new file at repo root
- Git tag `v1.0.0` on HEAD
