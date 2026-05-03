## Purpose
Harden the SSH daemon on Debian-based hosts and optionally manage operator SSH keys.

## Requirements

### Requirement: SSH daemon hardened unconditionally
The role SHALL set `PermitRootLogin no` and `PubkeyAuthentication yes` in `/etc/ssh/sshd_config` as its **first** tasks, before any key-management checks. This guarantees both settings are applied even if the play subsequently aborts (e.g. pre-check failure when `ssh_manage_keys: true`).

#### Scenario: Settings absent before role runs
- **WHEN** `/etc/ssh/sshd_config` does not contain `PermitRootLogin no` or `PubkeyAuthentication yes`
- **THEN** the role adds both lines and restarts sshd

#### Scenario: Settings already correct
- **WHEN** both lines are already present and correct
- **THEN** the role reports no change and does not restart sshd

### Requirement: Key management gated on ssh_manage_keys
When `ssh_manage_keys` is `true`, the role SHALL assert `{{ ssh_remote_user_home }}/.ssh/authorized_keys` (the `ansible_user`'s authorized_keys on the target host) is non-empty, deploy the operator's public key from `ssh_public_key_file` (a path on the control node), and set `PasswordAuthentication no`. When `false`, all three steps SHALL be skipped and `PasswordAuthentication` SHALL NOT be modified.

#### Scenario: ssh_manage_keys true — authorized_keys absent
- **WHEN** `ssh_manage_keys` is `true` and `{{ ssh_remote_user_home }}/.ssh/authorized_keys` is absent or empty on the target host
- **THEN** the role fails with a lockout-prevention message; `PermitRootLogin no` and `PubkeyAuthentication yes` will already have been applied (unconditional hardening runs first)

#### Scenario: ssh_manage_keys true — key present
- **WHEN** `ssh_manage_keys` is `true` and a valid pubkey is at `ssh_public_key_file`
- **THEN** the key is deployed and `PasswordAuthentication no` is set in sshd_config

#### Scenario: ssh_manage_keys false — no key on control node
- **WHEN** `ssh_manage_keys` is `false`
- **THEN** pre-check, key deployment, and `PasswordAuthentication no` are all skipped; existing `PasswordAuthentication` value is unchanged

### Requirement: sshd restarted on config change
The role SHALL restart the sshd service whenever `sshd_config` is modified.

#### Scenario: Config line changed
- **WHEN** any `lineinfile` task reports changed
- **THEN** the `Restart sshd` handler fires and sshd restarts

#### Scenario: Config unchanged
- **WHEN** all `lineinfile` tasks report ok
- **THEN** the handler does not fire
