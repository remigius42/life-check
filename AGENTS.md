# AGENTS.md

Target: Raspberry Pi running Raspberry Pi OS (Debian-based). Use `apt` modules.

## Project structure

- `playbooks/site.yml` — main playbook
- `playbooks/verify.yml` — assert expected post-state
- `roles/` — one role per concern

## Adding new roles

1. `ansible-galaxy init roles/<name>`
1. Implement `tasks/main.yml`; put configurable values in `defaults/main.yml`
1. **Variable naming:** prefix all vars with the role name (e.g., `<name>_foo`)
1. Delete unused dirs (`files/`, `templates/`, `handlers/`)
1. Add role to `playbooks/site.yml`
1. Add assert tasks to `playbooks/verify.yml`
