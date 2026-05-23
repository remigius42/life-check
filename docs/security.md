<!-- spellchecker:ignore avahi -->

# Security & Privacy

This document covers the security and privacy posture of the Life Check system.
It is intended for users who want to understand the design decisions before
deploying a device that monitors someone's daily routine.

## Threat model

The system is designed for a trusted home LAN. The primary threats are:

- **Compromised or malicious device on the same LAN** — any device with LAN
  access can reach the web UI and, on the Raspberry Pi route, control it without
  authentication
- **Malicious WiFi guest** — same access as above while on the network
- **Behavioral inference** — crossing counts and even binary ok/not_ok signals
  reveal daily routines over time; any party with access to the web UI, webhook
  channel, or HA integration is a potential inference vector
- **Leaked webhook URL** — anyone with the URL receives daily reports

Physical access to the appliance and internet-originating attacks are both out
of scope: the system is not intended to be internet-reachable and no setup step
opens it to the internet.

## Privacy

Privacy is the primary design concern, because crossing counts are inherently
sensitive: they reveal daily routines, sleep patterns, and activity peaks. Even
a coarse binary signal (above threshold / below threshold) becomes identifying
over time.

### Behavioral inference and the exposure hierarchy

The three interfaces that expose data each carry a different inference risk, and
the system is deliberately designed with a tiered exposure model:

| Interface      | What is exposed                                 | Who can access it                                           |
| -------------- | ----------------------------------------------- | ----------------------------------------------------------- |
| Web UI         | Exact counts, 14-day history, live sensor state | Anyone on the LAN (RPi: no auth; ESP32: password-protected) |
| Webhook        | A configurable message, sent once per day       | Anyone with the webhook URL                                 |
| HA integration | Binary `ok`/`not_ok` within the privacy window  | HA automations and users                                    |

**Web UI** carries the highest inference risk: exact daily counts and a 14-day
history are visible to anyone who can reach it on the LAN. This is intentional —
it is the operator's interface. Restrict LAN access to the device if cohabitants
should not see this data.

**Webhook** sends one message per day. The default templates deliberately omit
the crossing count: a shared channel (Slack, Telegram, etc.) may be visible to
more people than intended, and exact numbers reveal more about someone's routine
than a simple "active today / not yet" signal. If you include `{count}` in a
template, treat the receiving channel as sensitive. The webhook URL itself is a
credential — it grants the ability to read all future reports. Store it in
ansible-vault (RPi) or `esphome/secrets.yaml` (ESP32) and never commit it.

**HA integration** is the lowest-resolution interface by design: only a binary
state is exposed, gated behind the privacy window and jitter (see below). This
is the recommended channel for automated alerting: it reveals the minimum
necessary to answer "has the person been active today?"

### Privacy window

The Home Assistant sensor operates within a **daytime window** only (default
17:00–08:00). Outside this window the sensor always returns `not_ok` / **OFF**,
regardless of the actual beam count. Nighttime activity is structurally
invisible — the signal is eliminated, not merely obscured. Jitter alone cannot
achieve this: even a 60-minute smear leaves habitual patterns detectable across
weeks of HA history.

### Jitter

Within the daytime window, the transition to `ok` / **ON** is delayed by a
random jitter of **15–60 minutes**. This prevents a live observer from inferring
the exact time of the first qualifying crossing.

Both the privacy window end time and the jitter range are **compile-time
parameters** on the ESP32 route and **deploy-time Ansible variables** on the
Raspberry Pi route. A Home Assistant actor cannot shrink either parameter at
runtime.

### What the HA integration exposes

The raw crossing count and 14-day history are not exposed to HA. The webhook URL
is marked `internal: true` and is invisible to HA. Message templates are visible
to HA as editable text entities, but they contain only the template string (e.g.
`"Active today ✅"`) — the `{count}` substitution happens at report time and the
resolved count is never sent to HA.

## Network security

- **LAN isolation** — UFW (RPi) enforces a deny-all inbound policy; SSH and the
  web UI port are allowed only from the configured LAN subnet. The ESP32 is
  similarly unreachable from the internet by default (no port forwarding
  configured).
- **No inbound internet access** — neither route opens any port to the internet.
  The system initiates all outbound connections.
- **Outbound webhook traffic** — sent over HTTPS to the configured webhook URL.
  The ESP32 route verifies the server certificate; the Raspberry Pi route uses
  the system CA bundle via Python's `ssl` module.
- **mDNS discovery** — both routes advertise via mDNS (`avahi` on RPi, ESPHome's
  built-in mDNS on ESP32). This is LAN-only and is how `<hostname>.local`
  resolution works.

## Appliance security

### Raspberry Pi

- **SSH hardening** — the `ssh` role sets `PermitRootLogin no` and
  `PubkeyAuthentication yes`. When `ssh_manage_keys: true` (default),
  `PasswordAuthentication no` is also enforced and the operator's public key is
  deployed. See the [ssh role README](../roles/ssh/README.md).
- **Firewall** — the `ufw` role applies a deny-all inbound policy and allows SSH
  (port 22) and the web UI port from the LAN subnet only. See the [ufw role
  README](../roles/ufw/README.md).
- **Brute-force protection** — fail2ban jails SSH with configurable ban time,
  find time, and max retries (defaults: 1 h / 10 min / 5). Optional Slack alerts
  on ban events. See the [fail2ban role README](../roles/fail2ban/README.md).
- **Secrets at rest** — webhook URLs and other secrets are stored in
  `group_vars/all/vault.yml`, encrypted with ansible-vault. The vault password
  file (`.vault_pass`) is gitignored and chmod 600.

### ESP32

- **OTA password** — required before any over-the-air firmware update. Set in
  `esphome/secrets.yaml` before first flash.
- **Home Assistant API encryption** — the ESPHome native API uses the Noise
  protocol (AES-128-GCM). Set `api_encryption_key` in `esphome/secrets.yaml`
  before first flash (generate with `openssl rand -base64 32`).
- **Secrets at compile time** — `esphome/secrets.yaml` holds WiFi credentials,
  OTA password, web UI password, webhook URL, and API key. It is gitignored and
  must never be committed.

## Application security

### Raspberry Pi web UI

The web UI (port 8080, LAN-only) has **no authentication**. HTTP Basic Auth
without TLS is base64-encoded credentials in cleartext — trivially readable by
any passive observer on the same L2 segment. The actual access control is the
UFW firewall restricting the port to the LAN subnet. Adding a password over
plain HTTP would provide a false sense of security without meaningful protection
against any network-level threat.

One consequence worth stating explicitly: the manual reset button and test mode
are accessible to anyone on the LAN. A LAN-local party could reset the day's
count to hide a low-crossing day. This is an accepted trade-off given the
trusted home LAN threat model.

If unauthenticated LAN access is unacceptable in your environment, you can add a
reverse proxy with TLS and Basic Auth in front of the web UI. The daemon binds
to all interfaces (`0.0.0.0`) and relies on UFW for access control; it is not
intended to be internet-facing.

### ESP32 web UI

The web UI (port 80) is protected by HTTP Basic Auth configured in
`esphome/secrets.yaml`. The same cleartext caveat applies: credentials travel
unencrypted. The password provides a friction barrier against casual or
accidental access — not protection against a network adversary. ESPHome includes
this capability at no setup cost, so it is enabled by default.

### Vulnerability reporting

See [SECURITY.md](../.github/SECURITY.md) for how to report vulnerabilities
privately.

## Data security

- **Minimal collection** — the only data recorded is an integer crossing count
  per day, retained for 14 days. No names, timestamps of individual crossings,
  audio, video, or other PII are stored anywhere in the system.
- **Persistence** — on the Raspberry Pi route, the 14-day history survives
  reboots. On the ESP32 route, the 14-day history resets on reboot; today's
  count is preserved in non-volatile storage.
- **No remote logging** — neither route sends data anywhere except the
  configured webhook URL, once per day.

## Supply chain

No pre-built firmware binaries are distributed. Users compile from source using
ESPHome (ESP32 route) or run the Ansible playbook against a stock Raspberry Pi
OS image (RPi route).

This is an intentional policy. Distributing opaque, LAN-connected firmware
contradicts the project's purpose: a device that monitors someone's daily
routine must be transparent. Pre-built binaries would require users to trust the
build environment, the CI pipeline, and the maintainer's account security
without the ability to verify what is actually running on the device. Compiling
from source gives users full visibility into what they are deploying.

There is also a practical reason: ESPHome bakes WiFi credentials, OTA password,
web UI password, and the HA API key into the firmware at compile time. A
CI-built binary would use the placeholder values from `secrets.yaml.example`:
the WiFi credentials won't match the user's network, the webhook URL is a
non-functional placeholder, and the OTA password, web password, and API
encryption key are publicly known defaults that defeat the security they are
meant to provide.
