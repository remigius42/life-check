## ADDED Requirements

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
The role SHALL deploy `beam-detector-report.service.j2` and `beam-detector-report.timer.j2` to `/etc/systemd/system/` via `ansible.builtin.template`. The timer SHALL be enabled and started via `ansible.builtin.systemd enabled=true state=started` so it is active in the current session and fires at the next scheduled wall-clock time (starting the timer unit does not invoke the service immediately). Changing either unit file SHALL notify the `Reload systemd` handler (daemon-reload).

Required content of `beam-detector-report.service.j2`:
- `Type=oneshot`
- `ExecStart=/usr/bin/python3 {{ detector_install_dir }}/reporter.py`
- `User={{ detector_report_user }}`
- `Group={{ detector_group }}`
- `WorkingDirectory={{ detector_install_dir }}`
- `EnvironmentFile={{ detector_install_dir }}/.env.report` containing `DETECTOR_REPORT_WEBHOOK_URL` (mode 0600, owner `{{ detector_report_user }}`) — keeps the secret out of the world-readable unit file
- `Environment=` lines for `DETECTOR_REPORT_THRESHOLD`, `DETECTOR_REPORT_MSG_OK`, `DETECTOR_REPORT_MSG_LOW`, `DETECTOR_REPORT_MSG_ZERO`, `DETECTOR_COUNTS_PATH` — message values SHALL be quoted in the unit file to handle spaces

Required content of `beam-detector-report.timer.j2`:
- `OnCalendar={{ detector_report_time }}` (wall-clock schedule)
- `Persistent=true` (fire immediately when the timer unit is activated if its last trigger time was missed — e.g., while the host was powered off)
- `Unit=beam-detector-report.service`
- `[Install]` section with `WantedBy=timers.target` (required so `systemctl enable` creates the activation symlink)

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
- `detector_report_user`: `"beam-detector-report"` (system user that runs the reporter)
- `detector_counts_path`: `"{{ detector_data_dir }}/counts.json"` (shared with the daemon; already defined in `detector-core` defaults)

Non-secret variables are passed to `reporter.py` as `Environment=` entries in `beam-detector-report.service.j2`. The webhook URL is passed via `EnvironmentFile=` pointing to a separate secrets file (mode 0600). The reporter reads all of them from `os.environ`.

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
