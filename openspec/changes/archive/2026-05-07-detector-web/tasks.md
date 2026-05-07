## 1. Role Variables and Static Assets

- [x] 1.1 Add web variables to `roles/detector/defaults/main.yml`: `detector_web_port: 8080`, `detector_state_path: "{{ detector_run_dir }}/state.json"`, `detector_pico_version: "2.1.1"`, `detector_web_user: "beam-detector-web"`, `detector_group: "detector"`; note that `ufw_lan_subnet` is required from a higher scope (e.g. `group_vars/all/vars.yml`) and is not defined in this role
- [x] 1.2 Download `pico.min.css` v`{{ detector_pico_version }}` from the Pico CSS GitHub releases and vendor it at `roles/detector/files/static/pico-{{ detector_pico_version }}.min.css` (version in filename for cache busting and auditability; commit to repo — no internet needed at deploy time; default version is set by `detector_pico_version` in `defaults/main.yml`)

## 2. Web Server Script

- [x] 2.1 Write `roles/detector/files/web.py`: Flask app with `GET /` (full status page with inline JS `EventSource`), `GET /stream` (SSE generator: reads `state.json` via `_read_state()` every 50 ms — catch `OSError` at debug level and `JSONDecodeError` at warning level, return default state on error, never re-raise; wrap `yield` in `try/except GeneratorExit` to clean up on client disconnect; push JSON event only on change), `POST /test-mode/enable` (mkdir sentinel parent, touch sentinel, return 303 redirect to `/`; return 500 on OSError), `POST /test-mode/disable` (unlink sentinel, return 303 redirect to `/`; return 500 on OSError), bind to `0.0.0.0` on port from env var
- [x] 2.2 Write inline HTML + JS in `web.py`: page shows beam state indicator, count, test mode badge, toggle button; ~10 lines vanilla JS `EventSource` connecting to `/stream` and updating DOM elements on each event; no external JS library
- [x] 2.3 Verify script starts locally: `DETECTOR_WEB_PORT=8080 python3 roles/detector/files/web.py` (confirm `GET /` returns 200 and `GET /stream` returns `text/event-stream`)

## 3. Systemd Service

- [x] 3.0 Update `roles/detector/templates/beam-detector.service.j2` (from detector-core): add `Group={{ detector_group }}` and `RuntimeDirectoryMode=2775` so `/run/beam_detector/` is created group-writable with the setgid bit; this allows `{{ detector_web_user }}` (member of `{{ detector_group }}`) to create and delete the sentinel file without root
- [x] 3.1 Write `roles/detector/templates/beam-detector-web.service.j2` with all required unit sections: `[Unit]` with `Description=` and `After=network.target` (no `After=beam-detector.service` — web server handles missing state files gracefully, per design Decision #7); `[Service]` with `Type=simple`, `User={{ detector_web_user }}`, `Group={{ detector_group }}`, `ExecStart=/usr/bin/python3 {{ detector_install_dir }}/web.py`, `Environment=` lines for `DETECTOR_WEB_PORT`, `DETECTOR_STATE_PATH`, `DETECTOR_SENTINEL`, `DETECTOR_COUNTS_PATH`, `DETECTOR_STATIC_DIR`, `DETECTOR_PICO_CSS`, `Restart=on-failure`; `[Install]` with `WantedBy=multi-user.target`

## 4. Ansible Tasks and Handlers

- [x] 4.1 Add to `roles/detector/tasks/main.yml`: create `detector` system group (`ansible.builtin.group`); create `beam-detector-web` system user (no shell, home `/nonexistent`, groups `[{{ detector_group }}]`) via `ansible.builtin.user`; set `/run/beam_detector/` owner/group/mode (`root:{{ detector_group }}` `2775`) and `/var/lib/beam_detector/` to (`root:{{ detector_group }}` `750`) via `ansible.builtin.file`; `apt` install `python3-flask`; create `{{ detector_install_dir }}/static/` directory; `copy` `pico-{{ detector_pico_version }}.min.css`; `copy` web.py (`owner=root`, `group={{ detector_group }}`, `mode=0755`); `template` beam-detector-web.service.j2 and updated beam-detector.service.j2 (both notify `Reload systemd`); `service` enable+start `beam-detector-web`; `community.general.ufw` rule for `detector_web_port` from `ufw_lan_subnet`
- [x] 4.2 Add handler to `roles/detector/handlers/main.yml`: `Restart beam-detector-web` (triggered by web.py or service unit changes)

## 5. Playbook Integration

- [x] 5.1 Add verify task to `playbooks/verify.yml`: assert `beam-detector-web.service` is running and enabled in `ansible_facts.services`

## 6. Web Server Tests

- [x] 6.1 Write `roles/detector/files/tests/test_web.py`: cover `_read_state` (file not found → default state; OSError → default state; JSONDecodeError → default state + warning; valid JSON → parsed state); cover toggle endpoints via `app.test_client()` (POST `/test-mode/enable` creates sentinel → 303; POST `/test-mode/disable` removes sentinel → 303; OSError on create → 500; OSError on delete → 500); cover `GET /` returns 200 with HTML content; cover `GET /stream` returns `text/event-stream` content type
- [x] 6.2 Run tests locally: `python3 -m unittest discover -s roles/detector/files/tests -p test_web.py -v` (all pass)

## 8. Dev Environment

- [x] 8.1 Create `requirements-dev.txt` in the repo root listing `flask` and `waitress` (packages needed to run `test_web.py` locally; Pi uses apt equivalents at deploy time)
- [x] 8.2 Run tests via the venv: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt && python3 -m unittest discover -s roles/detector/files/tests -p test_web.py -v` (all pass)

## 7. Documentation

- [x] 7.1 Add new web variables to `roles/detector/README.md` Role Variables table: `detector_web_port`, `detector_state_path` (note: already exists — verify), `detector_pico_version`, `detector_web_user`
