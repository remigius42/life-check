## ADDED Requirements

### Requirement: Role captures project version from git at deploy time
The role SHALL set a fact `detector_version` on the control host by running `git describe --tags` via `lookup('pipe', ...)`. Using `--tags` ensures both annotated and lightweight tags are resolved; the `initial` lightweight tag present since the first commit guarantees this always succeeds.

#### Scenario: Version resolved from tag
- **WHEN** the playbook runs on the repo
- **THEN** `detector_version` is set to the output of `git describe --tags` (e.g. `v2.2.1` or `v2.2.1-3-g543b3e5`)

### Requirement: verify.yml asserts DETECTOR_VERSION is deployed
`playbooks/verify.yml` SHALL assert that `DETECTOR_VERSION=` is present in the deployed `beam-detector-web.service` unit file, and that the rendered web UI HTML contains the version string.

#### Scenario: Unit file assertion passes
- **WHEN** `playbooks/verify.yml` runs after `playbooks/site.yml`
- **THEN** the assertion that `DETECTOR_VERSION=` appears in the unit file passes without failure

#### Scenario: Web UI assertion passes
- **WHEN** `playbooks/verify.yml` runs after `playbooks/site.yml`
- **THEN** the assertion that the version string appears in the rendered web UI HTML passes without failure

## MODIFIED Requirements

### Requirement: Role deploys web systemd service
The role SHALL deploy `beam-detector-web.service.j2` to `/etc/systemd/system/` as a `Type=simple` service running `web.py` as `User=beam-detector-web`, `Group=detector`. The service SHALL be enabled and started. Changing the unit SHALL trigger a `systemd daemon-reload` and service restart. The unit SHALL include `Environment=DETECTOR_VERSION={{ detector_version }}` so the web process can read the deployed version at runtime.

#### Scenario: Web service running and enabled after role run
- **WHEN** the role is applied
- **THEN** `beam-detector-web.service` is in state `running` and `enabled`

#### Scenario: DETECTOR_VERSION injected into service environment
- **WHEN** the role is applied
- **THEN** the deployed `beam-detector-web.service` unit contains `DETECTOR_VERSION` set to the value of `git describe` captured at run time
