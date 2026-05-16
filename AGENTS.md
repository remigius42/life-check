# AGENTS.md

Targets: Raspberry Pi OS (Debian-based, use `apt` modules) and ESP32 (ESPHome YAML in `esphome/`).

## Project structure

- `playbooks/site.yml` — main playbook
- `playbooks/verify.yml` — assert expected post-state
- `roles/` — one role per concern
- `esphome/life-check.yaml` — ESP32 firmware (ESPHome)
- `esphome/packages/` — reusable ESPHome package fragments (e.g. `ttgo.yaml`)
- `esphome/secrets.yaml` — copy from `secrets.yaml.example`; never committed

## Adding new roles

1. `ansible-galaxy init roles/<name>`
1. Convert `README.md` headings from Setext (`===`/`---`) to ATX (`#`/`##`)
1. Implement `tasks/main.yml`; put configurable values in `defaults/main.yml`
1. **Variable naming:** prefix all vars with the role name (e.g., `<name>_foo`)
1. Delete unused dirs (`files/`, `templates/`, `handlers/`)
1. Add role to `playbooks/site.yml`
1. Add assert tasks to `playbooks/verify.yml`

## Python tooling

Python files are formatted with **Black** and linted with **Ruff**; type-checked with **Pyright**
(`standard` mode). All three run as pre-commit hooks — do not bypass them.

- Configuration lives in `pyproject.toml` at the repo root (`[tool.black]`, `[tool.ruff]`, `[tool.pyright]`)
- Scripts are deployed verbatim (not as Jinja2 templates) so they can be imported and tested without Ansible
- `RPi.GPIO` is hardware-only; `reportMissingModuleSource` is suppressed in the Pyright config
- Dev dependencies (e.g. `flask`, `waitress`) are in `requirements-dev.txt`
  run tests via `.venv/bin/python3` — the system Python lacks these packages
- Black/Ruff/Pyright do **not** apply to ESPHome YAML files

## ESPHome firmware

The `esphome/` tree is compiled with `.venv/bin/esphome compile esphome/life-check.yaml`.
Optional TTGO OLED package: uncomment the `packages:` block in `life-check.yaml` (see `docs/esp32.md`).
