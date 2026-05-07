## ADDED Requirements

### Requirement: Role installs Flask
The `detector` Ansible role SHALL install `python3-flask` via apt.

#### Scenario: Flask installed after role run
- **WHEN** the role is applied
- **THEN** `python3-flask` is present in the installed package list

### Requirement: Role deploys web server script
The role SHALL deploy `web.py` to `{{ detector_install_dir }}/web.py` as a plain file via `ansible.builtin.copy`. Changing the script SHALL trigger a restart of `beam-detector-web.service`.

#### Scenario: Web script present after role run
- **WHEN** the role is applied
- **THEN** `/opt/beam_detector/web.py` exists on the target

### Requirement: Role creates detector group and web server user
The role SHALL create a `detector` system group and a `beam-detector-web` system user (no login shell, home directory `/nonexistent`, member of the `detector` group). The daemon service unit (`beam-detector.service`) SHALL be updated to add `Group=detector` and `RuntimeDirectoryMode=2775` so `/run/beam_detector/` is created group-writable with the setgid bit, allowing the unprivileged web server user to create and delete the sentinel file.

#### Scenario: Group and user present after role run
- **WHEN** the role is applied
- **THEN** the `detector` group exists and `beam-detector-web` is a member

### Requirement: Role deploys web systemd service
The role SHALL deploy `beam-detector-web.service.j2` to `/etc/systemd/system/` as a `Type=simple` service running `web.py` as `User=beam-detector-web`, `Group=detector`. The service SHALL be enabled and started. Changing the unit SHALL trigger a `systemd daemon-reload` and service restart.

#### Scenario: Web service running and enabled after role run
- **WHEN** the role is applied
- **THEN** `beam-detector-web.service` is in state `running` and `enabled`

### Requirement: Role adds UFW rule for web port
The role SHALL add a UFW rule via `community.general.ufw` allowing TCP on `{{ detector_web_port }}` from `{{ ufw_lan_subnet }}`.

#### Scenario: UFW rule present after role run
- **WHEN** the role is applied
- **THEN** a UFW rule permits TCP on `detector_web_port` from `ufw_lan_subnet`

### Requirement: Role vendors and serves Pico CSS
The role SHALL include `pico-{{ detector_pico_version }}.min.css` as a vendored static file under `roles/detector/files/static/` and copy it to `{{ detector_install_dir }}/static/pico-{{ detector_pico_version }}.min.css`. The version SHALL be included in the filename for cache busting and auditability. Flask SHALL serve it at `/static/pico-{{ detector_pico_version }}.min.css`. The filename SHALL be passed to the web server via the `DETECTOR_PICO_CSS` environment variable in the systemd unit. No internet access SHALL be required at deploy time or runtime.

#### Scenario: Pico CSS available after role run
- **WHEN** the role is applied
- **THEN** `{{ detector_install_dir }}/static/pico-{{ detector_pico_version }}.min.css` exists on the target and is served at the correct versioned path

### Requirement: Role adds web variables to defaults
The following variables SHALL be defined in `roles/detector/defaults/main.yml` with the stated defaults:

- `detector_web_port`: `8080`
- `detector_state_path`: `"{{ detector_run_dir }}/state.json"` (read by SSE generator)
- `detector_pico_version`: current pinned Pico CSS version (e.g. `2.1.1`)
- `detector_web_user`: `"beam-detector-web"` (non-root system user running the web service)
- `detector_group`: `"detector"` (shared group granting write access to `/run/beam_detector/`)

#### Scenario: Web variables have defaults
- **WHEN** the role is applied with no overrides
- **THEN** the web server binds to port 8080 and reads state from the default tmpfs path

### Requirement: verify.yml asserts web service is running
`playbooks/verify.yml` SHALL assert that `beam-detector-web.service` is running and enabled.

#### Scenario: Web service assertion passes
- **WHEN** `playbooks/verify.yml` runs after `playbooks/site.yml`
- **THEN** the `beam-detector-web.service` assertion passes without failure
