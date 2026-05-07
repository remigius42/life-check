# Development

Local setup for working on this project: dev environment, running tests,
linting, commit conventions, and the OpenSpec change workflow used to evolve the
codebase.

## Dev environment

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
docs: update DEVELOPMENT.md
```

## OpenSpec workflow

Changes are managed with [OpenSpec](https://openspec.dev). The typical cycle:

```bash
openspec new          # create a new change (proposal → design → specs → tasks)
openspec apply        # work through implementation tasks
openspec verify       # check completeness/correctness/coherence before archiving
openspec archive      # finalize the change
```

Changes live under `openspec/changes/<name>/`. Main specs live under `openspec/specs/`.
