> See also: [notes/impl.md](notes/impl.md) — safe Ansible lookup syntax and placement

## 1. Ansible Role

- [x] 1.1 Add `set_fact` task in `roles/detector/tasks/main.yml` to capture
  `detector_version` via `lookup('pipe', 'git describe --tags')`
- [x] 1.2 Add `Environment=DETECTOR_VERSION={{ detector_version }}` to
  `roles/detector/templates/beam-detector-web.service.j2`
- [x] 1.3 Extend `playbooks/verify.yml`: assert `DETECTOR_VERSION=` is present in
  the deployed unit file (same pattern as `DETECTOR_RESET_SENTINEL` check), and
  assert the version string appears in the rendered web UI HTML

## 2. Flask Web UI

- [x] 2.1 Add `DETECTOR_VERSION = os.environ.get("DETECTOR_VERSION", "unknown")`
  to `roles/detector/files/web.py`
- [x] 2.2 Render version string in footer next to the GitHub link in `web.py`
- [x] 2.3 Add test coverage for version display in
  `roles/detector/files/tests/test_web.py`

## 3. Release Bookkeeping

- [x] 3.1 Update `esphome/life-check.yaml` `esphome.project.version` to `2.3.0`
- [x] 3.2 Add `[2.3.0]` release section to `CHANGELOG.md` (move from Unreleased)
- [x] 3.3 Create annotated git tag `v2.3.0` _(done manually by user)_
