## ADDED Requirements

### Requirement: CHANGELOG.md at repo root
The project SHALL maintain a `CHANGELOG.md` at the repository root following [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) format with semantic versioning (MAJOR.MINOR.PATCH). The file SHALL include an `[Unreleased]` section at the top for changes not yet tagged.

#### Scenario: Changelog present in repo
- **WHEN** a user clones the repository
- **THEN** a `CHANGELOG.md` is present at the root with at least a `[1.0.0]` entry

---

### Requirement: Every OpenSpec change includes a changelog entry
Every OpenSpec change (i.e. work tracked in `openspec/changes/`) that is applied to main SHALL include an entry in `CHANGELOG.md` under the appropriate section (Added, Changed, Deprecated, Removed, Fixed, Security). Hotfixes and minor commits pushed directly to main without an OpenSpec change do not require a changelog entry. Breaking changes SHALL be marked with **BREAKING** and SHALL increment the MAJOR version.

#### Scenario: Breaking OpenSpec change applied
- **WHEN** an OpenSpec change that breaks existing deployments is applied to main
- **THEN** the MAJOR version is incremented and the changelog entry is marked **BREAKING**, noting which route(s) are affected

#### Scenario: Non-breaking OpenSpec change applied
- **WHEN** a non-breaking OpenSpec change is applied to main
- **THEN** the MINOR or PATCH version is incremented according to semver rules

---

### Requirement: v1.0.0 git tag on baseline commit
The commit representing the stable baseline state of both routes (ESP32/ESPHome and Raspberry Pi/Ansible) SHALL be tagged `v1.0.0` in git.

#### Scenario: Tag exists
- **WHEN** a user runs `git tag`
- **THEN** `v1.0.0` is listed and points to the baseline HEAD commit
