## Why

The `life_man_switch` Pi needs SSH hardened (no root login, pubkey-only where possible). The control node may not always have an SSH key available (e.g. a Windows machine accessed via TeamViewer), so the key-deploy + password-auth-disable flow must be optional rather than mandatory.

## What Changes

- New `roles/ssh/` Ansible role with `ssh_manage_keys` flag
- When `ssh_manage_keys: false`: skips pre-check, key deployment, and `PasswordAuthentication no` — still enforces `PermitRootLogin no` and `PubkeyAuthentication yes`
- `group_vars/all/vars.yml`: add `ssh_manage_keys: false`
- `playbooks/site.yml`: add `ssh` role
- `playbooks/verify.yml`: add sshd_config and service assertions (conditional on `ssh_manage_keys`)

## Capabilities

### New Capabilities

- `ssh`: SSH daemon hardening role with optional key management

### Modified Capabilities

- `site`: adds `ssh` role to the play
- `verify`: adds SSH post-state assertions

## Impact

- `roles/ssh/` (new): defaults, tasks, handlers, meta, README
- `group_vars/all/vars.yml`: one new variable
- `playbooks/site.yml`: one new role entry
- `playbooks/verify.yml`: new assertion block
- Requires `ansible.posix` collection — verify `collections/requirements.yml` includes it (see `notes/source-role.md`)
