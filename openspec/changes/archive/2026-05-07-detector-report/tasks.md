## 1. Role Variables

- [x] 1.1 Add report variables to `roles/detector/defaults/main.yml`: `detector_report_webhook_url` (default `""`), `detector_report_time` (default `"17:00"`), `detector_report_threshold` (default `2`), `detector_report_msg_ok` (default `"Beam breaks today: ✅ OK (equal or above threshold)"`), `detector_report_msg_low` (default `"Beam breaks today: 🚨 under threshold"`), `detector_report_msg_zero` (default `"Beam breaks today: 0 ⚠️ no breaks today, sensor might be down."`), `detector_counts_path` (default `/var/lib/beam_detector/counts.json`), `detector_report_user` (default `"beam-detector-report"`); add an inline comment on the three `msg_*` vars explaining that `{count}` is intentionally absent from the defaults for privacy and is available as an opt-in token
- [x] 1.2 Add `vault_detector_report_webhook_url: ""` to `group_vars/all/vault.yml` (encrypted)
- [x] 1.3 Add `detector_report_webhook_url: "{{ vault_detector_report_webhook_url | default('') }}"` to `group_vars/all/vars.yml`

## 2. Reporter Script

- [x] 2.1 Write `roles/detector/files/reporter.py`: configure `logging.basicConfig(stream=sys.stderr)` so systemd/journal captures all log output; read all config from `os.environ` (see task 3.1 for env var names); check `DETECTOR_REPORT_WEBHOOK_URL` first — if empty log warning and exit 0 (no counts.json read); check `DETECTOR_COUNTS_PATH` is set — if missing log error and exit 1 (config error); parse `DETECTOR_REPORT_THRESHOLD` as int with fallback to 1 and log a warning on parse failure; load `counts.json` from `DETECTOR_COUNTS_PATH` using `datetime.date.today()` (local timezone, consistent with daemon) — treat both missing file and `OSError` (including `PermissionError`) as → log warning + exit 0 (no POST), stale date → count=0, corrupt/non-dict/non-integer → count=0 + log warning; apply threshold logic in this exact order: `count == 0 → msg_zero`, `count < threshold → msg_low`, `else → msg_ok`; interpolate `{count}` via `str.format(count=N)` wrapped in `try/except (KeyError, ValueError)` — log error and exit 1 on failure; POST `{"text": message}` with `Content-Type: application/json` header via `urllib.request.urlopen(req, timeout=10)`; catch `urllib.error.HTTPError` (log HTTP status + up to 500 chars of response body decoded with `errors="replace"`), `urllib.error.URLError` (log reason), and any other `Exception` (log details), exit 1 on any network failure; exit 0 in all other cases
- [x] 2.2 Verify script runs locally: `python3 roles/detector/files/reporter.py` with no env vars set (should log a warning about webhook URL not set and exit 0, since the URL check runs before any file I/O)

## 3. Systemd Units

- [x] 3.1 Write `roles/detector/templates/beam-detector-report.service.j2` with all required systemd unit sections: `[Unit]` with `Description=`; `[Service]` with `Type=oneshot`, `ExecStart=/usr/bin/python3 {{ detector_install_dir }}/reporter.py`, `User={{ detector_report_user }}`, `Group={{ detector_group }}`, `WorkingDirectory={{ detector_install_dir }}`, and `EnvironmentFile={{ detector_install_dir }}/.env.report` for the webhook URL secret (mode 0600, owner `{{ detector_report_user }}`), and `Environment=` lines for `DETECTOR_REPORT_THRESHOLD`, `DETECTOR_REPORT_MSG_OK` (quoted), `DETECTOR_REPORT_MSG_LOW` (quoted), `DETECTOR_REPORT_MSG_ZERO` (quoted), `DETECTOR_COUNTS_PATH={{ detector_counts_path }}`; no `[Install]` section needed (the timer's `Unit=` directive activates the service)
- [x] 3.2 Write `roles/detector/templates/beam-detector-report.timer.j2` with all three systemd unit sections: `[Unit]` with `Description=`; `[Timer]` with `OnCalendar={{ detector_report_time }}` and `Persistent=true`; `[Install]` with `WantedBy=timers.target`

## 4. Ansible Tasks and Handlers

- [x] 4.0 Add `ansible.builtin.user` task to `roles/detector/tasks/main.yml`: create `{{ detector_report_user }}` system user (`shell: /usr/sbin/nologin`, `home: /nonexistent`, `groups: [{{ detector_group }}]`) — assumes `detector` group already exists (created in detector-core task 9.2)
- [x] 4.1 Add to `roles/detector/tasks/main.yml`: `copy` reporter.py (owner=root, group=`{{ detector_group }}`, mode=0755); `template` service unit (notifies `Reload systemd` handler); `template` timer unit (notifies `Reload systemd` and `Restart beam-detector-report.timer` handlers); `systemd` enable and start timer with `enabled=true state=started`
- [x] 4.2 Add `Restart beam-detector-report.timer` handler to `roles/detector/handlers/main.yml`: restarts the timer unit when its unit file changes so the new schedule takes effect in the current session without requiring a manual restart

## 5. Playbook Integration

- [x] 5.1 Add verify task to `playbooks/verify.yml`: assert `beam-detector-report.timer` is enabled in `ansible_facts.services` (the playbook already runs `service_facts` earlier; no additional `gather_facts` step needed for this assertion)

## 7. Documentation

- [x] 7.1 Add new report variables to `roles/detector/README.md` Role Variables table: `detector_report_user`, `detector_report_webhook_url`, `detector_report_time`, `detector_report_threshold`, `detector_report_msg_ok`, `detector_report_msg_low`, `detector_report_msg_zero`

## 6. Reporter Script Tests

- [x] 6.1 Write `roles/detector/files/tests/test_reporter.py`: cover `_read_count` (file not found → None; OSError → None; JSON decode error → 0 + warning; non-dict → 0 + warning; stale date → 0; non-int today_count → 0 + warning; today's count → value); cover `main` via `patch.dict(os.environ)` + mocked `urlopen` (no webhook URL → exit 0 + warning; no DETECTOR_COUNTS_PATH → exit 1; non-int threshold → warning + uses 1; count==0 → msg_zero sent; count < threshold → msg_low sent; count >= threshold → msg_ok sent; `{count}` token interpolated correctly; bad template key → exit 1); cover `_post` via mocked `urlopen` (HTTPError → exit 1 + logs status; URLError → exit 1 + logs reason; generic Exception → exit 1; success → no exception)
- [x] 6.2 Run tests locally: `python3 -m unittest discover -s roles/detector/files/tests -p test_reporter.py -v` (all pass)
