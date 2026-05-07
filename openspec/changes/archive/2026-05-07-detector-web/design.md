<!-- spellchecker: ignore distros htmx pipenv pydantic uvicorn werkzeug -->

## Context

`detector-core` writes `/var/lib/beam_detector/counts.json` (today's count + history) and exposes beam state via GPIO. Test mode is toggled via the sentinel file `/run/beam_detector/test_mode`. The web server reads both files; it does not talk to the daemon process directly. The existing `ufw` role manages firewall rules via `community.general.ufw` and defines `ufw_lan_subnet`. The `detector` Ansible role is extended (not a new role) to keep all detector concerns co-located.

## Goals / Non-Goals

**Goals:**
- Single-page status UI accessible from the LAN without authentication
- Show today's count and test mode status, updating live without full page reload
- Toggle test mode by writing/deleting the sentinel file
- UFW hole scoped to LAN subnet only
- Sub-2-second update latency for the break count

**Non-Goals:**
- Authentication or access control (LAN-only, trusted network assumed)
- Historical graphs or data export (out of scope)
- htmx polling (beam breaks last 100–500 ms; even 500 ms polling would miss most events — see Decision #2 for why SSE is used instead)
- HTTPS (LAN-only, certificate management overhead not justified)
- Reading live GPIO state directly (web server reads sentinel file, state.json, and counts.json only — no GPIO dependency; runs as an unprivileged user)

## Decisions

### 1. Flask over FastAPI / raw http.server

Flask ships as `python3-flask` in Raspberry Pi OS apt repos — no pip required. FastAPI needs `uvicorn` and `pydantic` which are not in apt. `http.server` could handle 3 routes but requires manual routing boilerplate and makes SSE responses ugly. Flask keeps `web.py` to ~50 readable lines and earns its place with SSE and the toggle endpoint in scope.

### 2. SSE over htmx polling or meta-refresh

`<meta http-equiv="refresh">` causes a full page reload — a beam break lasts 100–500 ms and would be invisible at any reasonable refresh interval.

htmx polling at even 500 ms would miss most breaks: the beam state flips and restores faster than the poll interval. A counter update landing in the 500 ms window after a break is a gamble, not a design.

**SSE (Server-Sent Events)** is the right fit: the Flask SSE generator reads `/run/beam_detector/state.json` from tmpfs every 50 ms and pushes an event to the browser whenever beam state or count changes. Worst-case browser latency ≈ 50 ms (poll interval) + ~1 ms (LAN RTT); average ≈ ~26 ms. The poll interval dominates — not network RTT. The browser `EventSource` API handles reconnection automatically. Note: `GET /` (the initial page render) reads `/var/lib/beam_detector/counts.json`; the SSE stream at `GET /stream` reads `state.json` — two different files, two different purposes.

Server side: one Flask generator function (~10 lines) returning `Response(mimetype='text/event-stream')`. Client side: ~5 lines of vanilla JS `EventSource` updating the DOM on each event. No external JS library needed.

### 3. Beam state: via state.json, not live GPIO

The web server runs as a separate process and must not access GPIO (GPIO is owned by the daemon). Beam state (broken/clear) is read from `state.json` on tmpfs — the same file the SSE stream polls. This avoids any GPIO dependency in the web server. What is omitted from this increment is *direct GPIO polling* by the web server and any GPIO-derived data not already present in `state.json`; the beam state field written by the daemon is sufficient for the status display.

### 4. Pico CSS for styling

**Decision:** Vendor Pico CSS (`pico-{{ detector_pico_version }}.min.css`) in the Ansible role under `roles/detector/files/static/` and copy it to `{{ detector_install_dir }}/static/pico-{{ detector_pico_version }}.min.css`, served by Flask at `/static/pico-{{ detector_pico_version }}.min.css`. (`detector_install_dir` is defined in `roles/detector/defaults/main.yml`, default `/opt/beam_detector`.)

Pico CSS is classless — linking it is sufficient for `<main>`, `<article>`, `<button>`, and `<section>` to look polished. No classes, no build step, no JS.

Alternatives considered: Water.css (unmaintained since 2021 — rejected), Bamboo CSS (1.9 KB, viable, but only 275 stars; Pico has 16.6k and active releases). The 7–9 KB size difference is irrelevant for a single LAN user.

Vendoring in the role (rather than `get_url` at deploy time) avoids a deploy-time internet dependency. The file is small (~10 KB) and changes infrequently. Version is pinned via the filename in `defaults/main.yml` (`detector_pico_version`).

### 5. Test mode toggle: POST endpoint writing/deleting sentinel file

A `POST /test-mode/enable` creates the sentinel file; `POST /test-mode/disable` deletes it. The status page renders a single button whose form action switches based on current state. No JavaScript required — standard HTML form POST.

The web server runs as a dedicated non-root system user (`detector_web_user`, default `beam-detector-web`) that is a member of a shared `detector` system group. The daemon continues to run as root (GPIO requires it). Directory permissions are:

| Path | Owner | Group | Mode |
|---|---|---|---|
| `/run/beam_detector/` | `root` | `detector` | `2775` (setgid) |
| `/var/lib/beam_detector/` | `{{ detector_service_user }}` | `detector` | `750` |

The setgid bit on `/run/beam_detector/` ensures new files (including the sentinel) inherit the `detector` group. The web server user can create and delete the sentinel via group-write on the directory without root. The `beam-detector.service` systemd unit sets `Group=detector` so the daemon runs with `detector` as its primary group and files it creates inherit the correct group.

Ansible creates the `detector` group and `beam-detector-web` user, and manages directory ownership and modes explicitly. `RuntimeDirectoryMode=2775` is set in the systemd unit (so the directory is created correctly on first boot) and Ansible also asserts the same mode on every redeployment — belt-and-suspenders.

### 6. UFW rule in detector role tasks, not ufw role

The UFW rule is specific to the detector web server. Adding it to the `ufw` role would couple unrelated concerns. The `detector` role tasks use `community.general.ufw` (already available via `collections/requirements.yml`) and reference the existing `ufw_lan_subnet` variable.

### 7. Separate systemd service, not combined with daemon

`beam-detector-web.service` is independent of `beam-detector.service`. They share files on disk but have no process-level coupling. Independent restart behavior is cleaner — a web server crash does not affect counting.

No `After=beam-detector.service` dependency is added: the web server handles missing `state.json` and `counts.json` gracefully — returning zero/false defaults — so it can start before the daemon has written its first file. This also means the web UI remains reachable if the daemon is stopped for maintenance.

### 8. Manual venv over uv/pipenv for dev dependencies

The test suite requires `flask` and `waitress` locally (the Pi uses apt packages; the dev machine does not). A dev venv is needed to run `test_web.py`.

**Decision:** plain `python3 -m venv .venv` + `pip install -r requirements-dev.txt`.

Alternatives considered:
- `uv` — fastest option with a proper lockfile, but requires installation via a curl-pipe-bash script on many distros, which is a security non-starter for a home infrastructure repo.
- `pipenv` — outdated; slow and stagnant since ~2020.
- `poetry` — solid but heavyweight for two dev-only packages.

The manual venv approach requires no extra tooling beyond the stdlib `venv` module and `pip`, is universally understood, and is reproducible via `requirements-dev.txt`. The venv is gitignored (already covered by `.gitignore`); `requirements-dev.txt` is committed.

## Risks / Trade-offs

- **No authentication** → mitigated by UFW rule restricting to LAN subnet; acceptable for a home/small-office deployment
- **Web server runs as non-root** → sentinel file access via `detector` group + setgid directory (see Decision 5); daemon stays root for GPIO; attack surface of the web process is limited to reading two files and creating/deleting one sentinel file
- **Sentinel file race between web toggle and daemon auto-revert** → last writer wins; acceptable given the auto-revert grace period (`detector_test_mode_grace_period_s`, default 1800 s / 30 min — the daemon deletes the sentinel after this idle timeout) and toggle is a deliberate user action
- **state.json / counts.json missing or corrupt on startup** → web server returns zero/false defaults (OSError) or logs a warning and falls back to defaults (JSONDecodeError); no crash, no user-visible error beyond stale values until the daemon writes its first file
- **state.json read without file locking** → the daemon writes both files atomically via temp-file-and-rename (the same guarantee used by `detector-core`); partial reads are not possible; no locking needed in the web server
- **counts.json read without file locking** → same atomic-rename guarantee from `detector-core`; no mitigation needed
- **SSE connection held open per browser tab** → one persistent connection per client; acceptable for a LAN-only single-user deployment; served by Waitress (`python3-waitress` apt package, no pip required) — consistent with the apt-only constraint and suitable for production unlike the Werkzeug dev server; `EventSource` reconnects automatically on disconnect

## Migration Plan

1. Run `ansible-playbook playbooks/site.yml` — installs Flask, deploys `web.py`, starts service, adds UFW rule
2. Access `http://<pi-ip>:{{ detector_web_port }}` from LAN browser to verify (`detector_web_port` default: `8080`, defined in `roles/detector/defaults/main.yml`)
3. Run `ansible-playbook playbooks/verify.yml` — asserts service running
4. Rollback: `systemctl disable --now beam-detector-web.service && ufw delete allow from {{ ufw_lan_subnet }} to any port {{ detector_web_port }} proto tcp`

## Open Questions

None.

## See Also

- `notes/implementation.md` — Flask SSE generator, EventSource JS snippet, toggle endpoint pattern (204), Waitress binding, systemd env var passing
