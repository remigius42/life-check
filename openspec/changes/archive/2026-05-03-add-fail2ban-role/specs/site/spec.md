## ADDED Requirements

### Requirement: fail2ban role applied in site.yml
`playbooks/site.yml` SHALL include the `fail2ban` role after `ufw`.

#### Scenario: Running site.yml applies fail2ban role
- **WHEN** `playbooks/site.yml` is executed
- **THEN** the `fail2ban` role runs against all hosts after the `ufw` role
