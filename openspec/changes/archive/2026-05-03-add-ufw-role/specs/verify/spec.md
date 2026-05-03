## ADDED Requirements

### Requirement: verify.yml asserts ufw post-state
`playbooks/verify.yml` SHALL assert that UFW is active after a successful `site.yml` run.

#### Scenario: Run verify after successful site.yml
- **WHEN** `playbooks/verify.yml` runs
- **THEN** `ufw status` reports `Status: active`
