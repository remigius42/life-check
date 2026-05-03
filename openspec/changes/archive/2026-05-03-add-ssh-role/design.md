<!-- spellchecker: ignore precheck -->

## Context

The standard SSH hardening pattern — assert `authorized_keys` is non-empty, deploy operator pubkey from control node, set `PasswordAuthentication no` / `PermitRootLogin no` / `PubkeyAuthentication yes` — assumes a key-capable control node. This project needs to support control nodes without an SSH key (e.g. a Windows machine accessed via TeamViewer), so key management must be optional. See `notes/source-role.md` for the reference implementation.

## Goals / Non-Goals

**Goals:**
- Apply `PermitRootLogin no` and `PubkeyAuthentication yes` unconditionally
- Gate lockout-risk tasks (pre-check, key deploy, `PasswordAuthentication no`) behind `ssh_manage_keys`
- Follow existing project conventions (per-task `become`, var prefix, remove unused dirs)

**Non-Goals:**
- Key generation or distribution to the control node
- UFW / fail2ban integration (separate roles)

## Decisions

**Single boolean `ssh_manage_keys`** over separate flags (e.g., `ssh_skip_precheck`, `ssh_skip_key_deploy`): the three gated tasks are semantically one unit — they only make sense together. One flag cannot get out of sync with itself.

**Task order — unconditional hardening first**: `PermitRootLogin no` and `PubkeyAuthentication yes` run before the key-management block. If the pre-check aborts the play (no authorized_keys), the host is left in a more hardened state rather than an untouched one. This makes the "unconditional" guarantee true regardless of what follows.

**`block:` wrapping pre-check + key deploy**: they are inseparable (pre-check exists solely to make key deploy safe). A block with `when: ssh_manage_keys` is cleaner than repeating `when` on each task.

**Separate `lineinfile` task for `PasswordAuthentication no`** (not in the loop with the other two settings): makes the conditional immediately visible; the loop carries unconditionally-safe settings only.

**`become: true` per-task** (not per-play): mirrors `roles/locales` convention; keeps privilege escalation scope minimal.

**`ssh_manage_keys: false` in `group_vars/all/vars.yml`**: documents the current deployment scenario explicitly; default in `defaults/main.yml` stays `true` so the role is correct for key-capable control nodes and can be switched on when the deployment context changes.

## Risks / Trade-offs

`PasswordAuthentication` left enabled (when `ssh_manage_keys: false`) → password brute-force risk. Mitigation: fail2ban role (separate) will handle this. **Deployment order matters**: fail2ban must be included in the same `site.yml` run as the ssh role (or deployed before) — running ssh in isolation with `ssh_manage_keys: false` leaves the host exposed until fail2ban is active.

## Migration Plan

No existing sshd_config on target to preserve — fresh Pi. Run `site.yml`, verify with `verify.yml`. Rollback: revert sshd_config manually or re-run without the role.
