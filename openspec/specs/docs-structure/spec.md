## Purpose
Define the documentation structure: which files live where and what each contains.

## Requirements

### Requirement: docs/ directory houses route guides and supplementary documentation

The project SHALL contain a `docs/` directory at the repository root with the
following files:

- `docs/raspberry-pi.md` — end-to-end Raspberry Pi guide: Parts list, Wiring,
  Prerequisites, Pi Zero, Setup, and Ansible roles
- `docs/esp32.md` — end-to-end ESP32 guide: Parts list, Wiring, Prerequisites,
  and Setup
- `docs/development.md` — developer setup, testing, linting, commit conventions,
  and the OpenSpec change workflow
- `docs/notifications.md` — webhook setup and notification service options

#### Scenario: Reader follows Raspberry Pi route end-to-end

- **WHEN** a reader chooses the Raspberry Pi route
- **THEN** they find everything needed in `docs/raspberry-pi.md`: parts,
  wiring, prerequisites, setup steps, and Ansible role reference

#### Scenario: Reader follows ESP32 route end-to-end

- **WHEN** a reader chooses the ESP32 route
- **THEN** they find everything needed in `docs/esp32.md`: parts, wiring,
  prerequisites, and ESPHome setup steps

#### Scenario: Developer locates development guide

- **WHEN** a developer looks for local setup instructions
- **THEN** they find `docs/development.md` with dev environment, test, lint,
  and commit convention instructions

#### Scenario: Developer locates notification setup guide

- **WHEN** a developer looks for webhook configuration instructions
- **THEN** they find `docs/notifications.md` with Slack and alternative
  service setup

### Requirement: README is a thin router

`README.md` SHALL contain a project overview, a deployment route comparison
table, and links to the route guides. It SHALL NOT contain route-specific
prerequisites, setup steps, or role references.

#### Scenario: Reader orients and picks a route from README

- **WHEN** a reader lands on the README
- **THEN** they find a project overview, a pros/cons comparison table, and
  direct links to `docs/raspberry-pi.md` and `docs/esp32.md`

#### Scenario: README links to development and notifications docs

- **WHEN** a reader follows the README links to development or notification docs
- **THEN** they are taken to `docs/development.md` and `docs/notifications.md`
  respectively
