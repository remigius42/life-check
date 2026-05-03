## Why

`ssh_manage_keys: false` leaves `PasswordAuthentication` enabled on this host. Even on a LAN-only Pi, ufw adds defense-in-depth by restricting all inbound traffic to explicitly allowed rules.

## What Changes

- New `roles/ufw/` Ansible role: deny-all inbound baseline, SSH from LAN subnet allowed
- `group_vars/all/vars.yml`: add `ufw_lan_subnet`
- `playbooks/site.yml`: add `ufw` role after `ssh`
- `playbooks/verify.yml`: add ufw active assertion

## Capabilities

### New Capabilities

- `ufw`: firewall role — deny-all inbound, allow SSH from LAN subnet

### Modified Capabilities

- `site`: adds `ufw` role to the play
- `verify`: adds ufw post-state assertion

## Impact

- `roles/ufw/` (new): defaults, tasks, meta, README
- `group_vars/all/vars.yml`: one new variable
- `playbooks/site.yml`: one new role entry
- `playbooks/verify.yml`: new assertion block
- Requires `community.general` collection — already in `collections/requirements.yml`
