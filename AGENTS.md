# AGENTS.md

Target: Raspberry Pi running Raspberry Pi OS (Debian-based). Use `apt` modules.

## Project structure

- `playbooks/site.yml` — main playbook
- `playbooks/verify.yml` — assert expected post-state
- `roles/` — one role per concern

## Python tooling

Python files are formatted with **Black** and linted with **Ruff**; type-checked with **Pyright**
(`standard` mode). All three run as pre-commit hooks — do not bypass them.

- Configuration lives in `pyproject.toml` at the repo root (`[tool.black]`, `[tool.ruff]`, `[tool.pyright]`)
- Scripts are deployed verbatim (not as Jinja2 templates) so they can be imported and tested without Ansible
- `RPi.GPIO` is hardware-only; `reportMissingModuleSource` is suppressed in the Pyright config

## Adding new roles

1. `ansible-galaxy init roles/<name>`
1. Convert `README.md` headings from Setext (`===`/`---`) to ATX (`#`/`##`)
1. Implement `tasks/main.yml`; put configurable values in `defaults/main.yml`
1. **Variable naming:** prefix all vars with the role name (e.g., `<name>_foo`)
1. Delete unused dirs (`files/`, `templates/`, `handlers/`)
1. Add role to `playbooks/site.yml`
1. Add assert tasks to `playbooks/verify.yml`
