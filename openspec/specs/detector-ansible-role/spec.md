## Purpose
Deploy and manage the beam-detector daemon via an Ansible role: install system packages, deploy scripts and config, create the `detector` group and required directories, and manage the systemd service.

## Requirements

### Requirement: Role installs required system packages
The `detector` Ansible role SHALL install `python3-rpi.gpio` via apt on the target host.

#### Scenario: Package installed after role run
- **WHEN** the role is applied to a host
- **THEN** `python3-rpi.gpio` is present in the installed package list

### Requirement: Role deploys daemon script and tests
The role SHALL deploy `detector.py` to `{{ detector_install_dir }}/detector.py` and `test_detector.py` to `{{ detector_install_dir }}/tests/test_detector.py`. Scripts SHALL be deployed as plain files (not Jinja2 templates) via `ansible.builtin.copy`. Changing the script SHALL trigger a service restart. Default: `detector_install_dir = /opt/beam_detector`.

#### Scenario: Script present after role run
- **WHEN** the role is applied
- **THEN** `{{ detector_install_dir }}/detector.py` exists on the target (default: `/opt/beam_detector/detector.py`)

### Requirement: Role deploys INI configuration from template
The role SHALL render `config.ini.j2` to `{{ detector_config_dir }}/config.ini`. All tunable parameters SHALL be sourced from role variables with defaults defined in `defaults/main.yml`. Changing the config SHALL trigger a service restart. The file SHALL be owned by `{{ detector_service_user }}:{{ detector_group }}` with mode `0640`, so the daemon process and all `detector`-group members can read it. Default: `detector_config_dir = /etc/beam_detector`.

#### Scenario: Config present after role run
- **WHEN** the role is applied
- **THEN** `{{ detector_config_dir }}/config.ini` (default: `/etc/beam_detector/config.ini`) exists, contains values from role variables, is owned by `root:detector` (defaults), and has mode `0640`

### Requirement: Role creates detector system group
The role SHALL create a `detector` system group (variable `detector_group`, default `"detector"`). This group is the shared IPC boundary: the daemon writes to `/run/beam_detector/` and `/var/lib/beam_detector/`; future services (reporter, web) run as users in this group to read those directories without requiring root. The variable SHALL be defined in `roles/detector/defaults/main.yml`.

#### Scenario: Group present after role run
- **WHEN** the role is applied
- **THEN** the `detector` group exists on the target

### Requirement: Role creates required directories
The role SHALL create the directories below with the specified owner, group, and mode:

| Path | Owner | Group | Mode |
|---|---|---|---|
| `{{ detector_install_dir }}/` | `root` | `root` | `0755` |
| `{{ detector_install_dir }}/tests/` | `root` | `root` | `0755` |
| `/var/lib/beam_detector/` | `{{ detector_service_user }}` | `{{ detector_group }}` | `0750` |
| `{{ detector_config_dir }}/` | `root` | `root` | `0755` |

`/run/beam_detector/` is NOT created by Ansible. It is managed exclusively by systemd via `RuntimeDirectory=beam_detector` and `RuntimeDirectoryMode=2775` in the service unit, so it is re-created with the correct mode and group on every service start and absent when the service is stopped. `/var/lib/beam_detector/` has mode `0750` so only root and members of `detector` can read it.

#### Scenario: Directories present after role run
- **WHEN** the role is applied
- **THEN** each directory above exists with the specified owner, group, and mode

### Requirement: Role deploys and manages systemd service
The role SHALL deploy `beam-detector.service` from a Jinja2 template to `/etc/systemd/system/`. The service SHALL be enabled and started. Changing the unit file SHALL trigger a `systemd daemon-reload` followed by a service restart. The unit SHALL include `Group={{ detector_group }}`, `RuntimeDirectory=beam_detector`, and `RuntimeDirectoryMode=2775` so `/run/beam_detector/` is created with the correct group and setgid bit on every service start. systemd is the sole authority for this directory; Ansible does not create it.

#### Scenario: Service running and enabled after role run
- **WHEN** the role is applied
- **THEN** `beam-detector.service` is in state `running` and `enabled`

### Requirement: Role variables follow naming convention
All role variables SHALL be prefixed with `detector_`. Defaults SHALL be defined in `roles/detector/defaults/main.yml`. No variable SHALL be required without a default (all have sensible defaults for the target hardware). `detector_group` (default `"detector"`) SHALL be defined here as it is the shared IPC group used by all detector services.

#### Scenario: Role applies with no overrides
- **WHEN** the role is included with no variable overrides
- **THEN** the role completes successfully using all default values

### Requirement: Role integrated into site and verify playbooks
The `detector` role SHALL be listed in `playbooks/site.yml` after `fail2ban`. `playbooks/verify.yml` SHALL include assertions for: package installed, script present, config present, data directory present, service running and enabled.

#### Scenario: Verify playbook confirms deployment
- **WHEN** `playbooks/verify.yml` is run after `playbooks/site.yml`
- **THEN** all detector assertions pass without failures

### Requirement: Role deploys reporter script
The `detector` role SHALL deploy `reporter.py` to `{{ detector_install_dir }}/reporter.py` via `ansible.builtin.copy` with `owner=root`, `group={{ detector_group }}`, `mode=0755`. Changing the script does NOT require a systemd action — `beam-detector-report.service` is `Type=oneshot` and reads the script fresh on each invocation.

#### Scenario: Reporter script present after role run
- **WHEN** the role is applied
- **THEN** `{{ detector_install_dir }}/reporter.py` exists on the target (default: `/opt/beam_detector/reporter.py`) with mode 0755

### Requirement: Role creates reporter system user
The role SHALL create a `beam-detector-report` system user (variable `detector_report_user`, default `"beam-detector-report"`; no login shell; home `/nonexistent`) and add it to `{{ detector_group }}`. This grants read access to `/var/lib/beam_detector/` (mode `0750`, group `detector`) without requiring root.

#### Scenario: Reporter user present after role run
- **WHEN** the role is applied
- **THEN** the `beam-detector-report` user exists and is a member of the `detector` group

### Requirement: Role deploys reporter systemd units
The role SHALL deploy `beam-detector-report.service.j2` and `beam-detector-report.timer.j2` to `/etc/systemd/system/` via `ansible.builtin.template`. The timer SHALL be enabled and started via `ansible.builtin.systemd enabled=true state=started`. Changing either unit file SHALL notify the `Reload systemd` handler (daemon-reload); changing the timer unit SHALL additionally notify the `Restart beam-detector-report.timer` handler so the new schedule takes effect in the current session.

Required content of `beam-detector-report.service.j2`:
- `Type=oneshot`
- `ExecStart=/usr/bin/python3 {{ detector_install_dir }}/reporter.py`
- `User={{ detector_report_user }}`
- `Group={{ detector_group }}`
- `WorkingDirectory={{ detector_install_dir }}`
- `EnvironmentFile={{ detector_install_dir }}/.env.report` containing `DETECTOR_REPORT_WEBHOOK_URL` (mode 0600, owner `{{ detector_report_user }}`)
- `Environment=` lines for `DETECTOR_REPORT_THRESHOLD`, `DETECTOR_REPORT_MSG_OK`, `DETECTOR_REPORT_MSG_LOW`, `DETECTOR_REPORT_MSG_ZERO`, `DETECTOR_COUNTS_PATH`

Required content of `beam-detector-report.timer.j2`:
- `OnCalendar={{ detector_report_time }}`
- `Persistent=true`
- `Unit=beam-detector-report.service`
- `[Install]` with `WantedBy=timers.target`

#### Scenario: Timer enabled after role run
- **WHEN** the role is applied
- **THEN** `beam-detector-report.timer` is in state `enabled`

### Requirement: Role adds report variables to defaults
The following variables SHALL be defined in `roles/detector/defaults/main.yml` with the stated defaults:

- `detector_report_webhook_url`: `""` (overridden via vault in group_vars)
- `detector_report_time`: `"17:00"`
- `detector_report_threshold`: `2`
- `detector_report_msg_ok`: `"Beam breaks today: ✅ OK (equal or above threshold)"`
- `detector_report_msg_low`: `"Beam breaks today: 🚨 under threshold"`
- `detector_report_msg_zero`: `"Beam breaks today: 0 ⚠️ no breaks today, sensor might be down."`
- `detector_report_user`: `"beam-detector-report"`
- `detector_counts_path`: `"{{ detector_data_dir }}/counts.json"`

Non-secret variables are passed to `reporter.py` as `Environment=` entries in `beam-detector-report.service.j2`. The webhook URL is passed via `EnvironmentFile=` pointing to a mode-0600 secrets file.

#### Scenario: Report variables have defaults
- **WHEN** the role is applied with no overrides
- **THEN** the service unit sets `DETECTOR_REPORT_THRESHOLD=2` and the default message templates in its environment

### Requirement: Vault-backed webhook URL wired through group_vars
`group_vars/all/vault.yml` SHALL contain `vault_detector_report_webhook_url` (encrypted). `group_vars/all/vars.yml` SHALL reference it as `detector_report_webhook_url: "{{ vault_detector_report_webhook_url | default('') }}"`.

#### Scenario: Webhook URL available to role
- **WHEN** the vault is decrypted during playbook run
- **THEN** `detector_report_webhook_url` resolves to the stored URL

### Requirement: verify.yml asserts timer is enabled
`playbooks/verify.yml` SHALL assert that `beam-detector-report.timer` is enabled.

#### Scenario: Timer enabled assertion passes
- **WHEN** `playbooks/verify.yml` runs after `playbooks/site.yml`
- **THEN** the `beam-detector-report.timer` assertion passes without failure
