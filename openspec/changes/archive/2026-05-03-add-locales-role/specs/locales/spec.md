## ADDED Requirements

## Purpose
Configure system locales and timezone on Debian-based hosts.

## Requirements

### Requirement: Locales package installed
The system SHALL ensure the `locales` package is present via apt.

#### Scenario: Package absent before role runs
- **WHEN** the `locales` package is not installed
- **THEN** the role installs it

#### Scenario: Package already installed
- **WHEN** the `locales` package is already installed
- **THEN** the role reports no change

### Requirement: Locales enabled in locale.gen
The system SHALL ensure each entry in `locales_locales` is uncommented and present in `/etc/locale.gen`, triggering `locale-gen` if any change is made.

#### Scenario: Locale line is commented out
- **WHEN** a locale line is commented in `/etc/locale.gen`
- **THEN** the role uncomments it and notifies the `regenerate locales` handler

#### Scenario: Locale line already enabled
- **WHEN** a locale line is already uncommented in `/etc/locale.gen`
- **THEN** the role reports no change and does not trigger `locale-gen`

### Requirement: Timezone set via timedatectl
The system SHALL set the timezone to the value of `locales_timezone` using `timedatectl set-timezone`.

#### Scenario: Timezone differs from desired
- **WHEN** the current system timezone differs from `locales_timezone`
- **THEN** the role sets the timezone to `locales_timezone`

#### Scenario: Timezone already correct
- **WHEN** the current system timezone matches `locales_timezone`
- **THEN** the role skips the set-timezone command

### Requirement: Verify playbook asserts post-state
The `playbooks/verify.yml` playbook SHALL assert that the locales role has been applied correctly.

#### Scenario: Run verify after successful site.yml
- **WHEN** `playbooks/verify.yml` is run after a successful `playbooks/site.yml` run
- **THEN** all assertions pass with no failures
