## Why

The life_man_switch Ansible project has no roles or playbooks yet. Adding the `locales` role bootstraps the project with its first deployable capability: consistent locale and timezone configuration on the target Raspberry Pi.

## What Changes

- New `roles/locales/` role (tasks, defaults, handlers, meta, tests, README)
- New `playbooks/site.yml` — first version, applies `locales` to all hosts
- New `group_vars/all/vars.yml` — overrides `locales_timezone` to `Europe/Zurich`
- New `playbooks/verify.yml` — asserts post-deploy locales/timezone state

## Capabilities

### New Capabilities

- `locales`: Installs the `locales` package, enables specified locales in `/etc/locale.gen`, and sets the system timezone via `timedatectl`.

### Modified Capabilities

## Impact

- Adds `roles/`, `playbooks/`, and `group_vars/` directories to the project root.
- No existing code affected.
- Depends on `apt` (Debian/Raspberry Pi OS) and `timedatectl` (systemd).
