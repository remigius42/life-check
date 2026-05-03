## Purpose
Orchestrate all roles against all hosts via `playbooks/site.yml`.

## Requirements

### Requirement: ssh role applied in site.yml
`playbooks/site.yml` SHALL include the `ssh` role after `locales`.

#### Scenario: Running site.yml applies ssh role
- **WHEN** `playbooks/site.yml` is executed
- **THEN** the `ssh` role runs against all hosts after the `locales` role

### Requirement: ufw role applied in site.yml
`playbooks/site.yml` SHALL include the `ufw` role after `ssh`.

#### Scenario: Running site.yml applies ufw role
- **WHEN** `playbooks/site.yml` is executed
- **THEN** the `ufw` role runs against all hosts after the `ssh` role

### Requirement: fail2ban role applied in site.yml
`playbooks/site.yml` SHALL include the `fail2ban` role after `ufw`.

#### Scenario: Running site.yml applies fail2ban role
- **WHEN** `playbooks/site.yml` is executed
- **THEN** the `fail2ban` role runs against all hosts after the `ufw` role
