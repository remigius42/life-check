## ADDED Requirements

### Requirement: ufw role applied in site.yml
`playbooks/site.yml` SHALL include the `ufw` role after `ssh`.

#### Scenario: Running site.yml applies ufw role
- **WHEN** `playbooks/site.yml` is executed
- **THEN** the `ufw` role runs against all hosts after the `ssh` role
