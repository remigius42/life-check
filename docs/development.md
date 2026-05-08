# Development

Local setup for working on this project: dev environment, running tests,
linting, commit conventions, and the OpenSpec change workflow used to evolve the
codebase.

## Dev environment

Requires Python 3.13+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install --hook-type pre-commit --hook-type commit-msg
```

The venv must be **active when committing** — the `detector-unit-tests`
pre-commit hook uses `language: system`, so it picks up whatever `python3` is on
`PATH`. Without the venv, the hook fails with `ModuleNotFoundError: flask`.

## Running tests

```bash
.venv/bin/python3 -m unittest discover -s roles/detector/files/tests -v
```

## Linting and formatting

Pre-commit runs automatically on `git commit`. To run manually:

```bash
pre-commit run --all-files
```

Hooks include: Black, Ruff, Pyright, ansible-lint, mdformat, markdownlint, cspell, shellcheck,
gitleaks, and openspec validation.

## Commit messages

Conventional Commits enforced by commitlint (`commitlint.config.js`). Examples:

```text
feat: add beam-detector web UI
fix: correct redirect status code to 303
docs: update docs/development.md
```

## CI

GitHub Actions runs all pre-commit hooks on every push to `main` and on pull
requests from branches in the same repository (fork PRs are excluded — they lack
access to repository secrets).

Two hooks use `language: system` and require setup steps before pre-commit runs:

- **openspec-validate** — needs the `openspec` Node.js CLI. The hook entry uses
  `npx --yes openspec`, so no explicit install step is needed; `npx` resolves
  the binary via Node.js 24 (pinned with `actions/setup-node`).
- **detector-unit-tests** — needs `flask` and other packages from
  `requirements-dev.txt`.
  The workflow installs them via `pip install -r requirements-dev.txt` after
  configuring Python 3.13 with `actions/setup-python`.
- **esphome-config-validate** — needs `esphome` from `requirements-dev.txt`
  (covered by the same `pip install` step). The hook copies
  `esphome/secrets.yaml.example` → `esphome/secrets.yaml` if absent, then runs
  `esphome config esphome/life-check.yaml` to validate the firmware YAML without
  building firmware. No additional CI step required.

A dummy `.vault_pass` is created in CI so ansible-lint's syntax checks don't
abort — `ansible.cfg` requires the file unconditionally but no decryption
happens during linting.

> Any new `language: system` hook must have a corresponding setup step added to
> `.github/workflows/ci.yml` before merging.

## ESPHome

### Install

ESPHome is included in `requirements-dev.txt`, so the standard dev setup installs it:

```bash
pip install -r requirements-dev.txt
```

### First flash

```bash
cp esphome/secrets.yaml.example esphome/secrets.yaml
# Fill in esphome/secrets.yaml with your WiFi credentials, timezone, and webhook URL
esphome run esphome/life-check.yaml
```

Connect the ESP32 via USB before running. ESPHome compiles the firmware and
flashes it over USB, then opens the serial log. `secrets.yaml` is gitignored —
never commit it.

### OTA updates

After first flash the device is reachable over WiFi. Subsequent firmware updates go over-the-air:

```bash
esphome run esphome/life-check.yaml
```

ESPHome discovers the device via mDNS and uploads wirelessly. No USB required.

### Validate YAML without building

```bash
esphome config esphome/life-check.yaml
```

This parses and validates the YAML (including `secrets.yaml`) without compiling.

## OpenSpec workflow

Changes are managed with [OpenSpec](https://openspec.dev). The typical cycle:

```bash
openspec new          # create a new change (proposal → design → specs → tasks)
openspec apply        # work through implementation tasks
openspec verify       # check completeness/correctness/coherence before archiving
openspec archive      # finalize the change
```

Changes live under `openspec/changes/<name>/`. Main specs live under `openspec/specs/`.
