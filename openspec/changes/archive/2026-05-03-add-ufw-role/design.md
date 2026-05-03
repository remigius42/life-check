## Context

This host has no internet-facing services, so the firewall policy is: deny all inbound, allow SSH from LAN subnet only.

## Goals / Non-Goals

**Goals:**
- Deny all inbound traffic by default
- Allow SSH from the configured LAN subnet
- Enable UFW at boot
- Validate `ufw_lan_subnet` before applying any rules

**Non-Goals:**
- App-layer port rules (this host has no exposed services)
- Internet-facing access modes
- fail2ban integration (separate role, separate change)

## Decisions

**No handlers:** UFW enable/disable is idempotent and stateless — no service restart needed. `community.general.ufw state: enabled` is safe to run repeatedly.

**Subnet validation first:** Asserts `ufw_lan_subnet` is defined, non-empty, and matches a valid CIDR before any rule is applied. A misconfigured subnet would silently block SSH access.

**No default for `ufw_lan_subnet`:** Forcing it to be set explicitly in `group_vars` prevents silent misconfiguration. The assertion catches the empty-string case.

**`become: true` per-task** (not per-play): matches project convention from `roles/locales` and `roles/ssh`.

## Risks / Trade-offs

Running `site.yml` with ufw role for the first time on a host already accessed via SSH: ufw is enabled with the SSH-from-LAN rule in place, so the active session is not dropped. Risk is low if `ufw_lan_subnet` matches the control node's subnet.
