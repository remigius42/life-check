## Purpose
Assert post-state of all applied roles via `playbooks/verify.yml`.

## Requirements

### Requirement: verify.yml asserts SSH post-state
`playbooks/verify.yml` SHALL assert the SSH role's post-state after a successful `site.yml` run.

#### Scenario: Run verify after successful site.yml (ssh_manage_keys false)
- **WHEN** `playbooks/verify.yml` runs with `ssh_manage_keys: false`
- **THEN** assertions pass: `PermitRootLogin no` present, `PubkeyAuthentication yes` present, `PasswordAuthentication no` absent, sshd service running

#### Scenario: Run verify after successful site.yml (ssh_manage_keys true)
- **WHEN** `playbooks/verify.yml` runs with `ssh_manage_keys: true`
- **THEN** assertions pass: `PermitRootLogin no` present, `PubkeyAuthentication yes` present, `PasswordAuthentication no` present, sshd service running

### Requirement: verify.yml asserts ufw post-state
`playbooks/verify.yml` SHALL assert that UFW is active after a successful `site.yml` run.

#### Scenario: Run verify after successful site.yml
- **WHEN** `playbooks/verify.yml` runs
- **THEN** `ufw status` reports `Status: active`
