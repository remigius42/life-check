## Context

life_man_switch is a new Ansible project targeting a Raspberry Pi running Raspberry Pi OS (Debian-based). No roles or playbooks exist yet.

Reference implementations for all role files are in `notes/` — see `notes/role-tasks.yml`, `notes/role-defaults.yml`, `notes/role-handlers.yml`, `notes/role-meta.yml`, and `notes/group-vars.yml`.

## Goals / Non-Goals

**Goals:**
- Implement the `locales` role using the reference files in `notes/` without modification
- Create a minimal `playbooks/site.yml` that applies the role
- Override `locales_timezone` to `Europe/Zurich` via `group_vars/all/vars.yml` (see `notes/group-vars.yml`)
- Create `playbooks/verify.yml` with assertions for the locales post-state

**Non-Goals:**
- Adding any other roles at this stage
- Modifying the locales role logic

## Decisions

**Implement from reference files in `notes/`**: The role files are provided verbatim in `notes/`. Copy them as-is — no adaptation needed.

**`group_vars/all/vars.yml` for timezone override**: Standard Ansible location for host-group variables. Works without an inventory if vars_files is referenced explicitly in the playbook.

**`vars_files` explicit load in playbook**: Avoids relying on Ansible's automatic group_vars discovery (which requires a matching inventory group), making the playbook portable.

## Risks / Trade-offs

- [locale-gen idempotency] Running `locale-gen` on every notify can be slow → acceptable; it only fires when locale.gen changes.
- [timedatectl availability] Requires systemd → guaranteed on Raspberry Pi OS.
