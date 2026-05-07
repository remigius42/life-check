## Context

Pre-commit hooks cover all linting, formatting, type-checking, and validation locally.
Two hooks use `language: system`: `openspec-validate` (Node.js CLI) and
`detector-unit-tests` (Python). GitHub-hosted runners include both Node.js and
Python, so both can be satisfied without a custom container.

## Goals / Non-Goals

**Goals:**

- Run all existing pre-commit hooks in CI on every push and non-fork PR to `main`
- Keep the workflow file minimal and dependency-free beyond what pre-commit already manages
- Avoid skipping any hooks

**Non-Goals:**

- Ansible linting beyond what ansible-lint's pre-commit hook already does
- Deployment or integration testing
- Matrix builds across Python/Node versions

## Decisions

**Use `pre-commit/action` rather than a bare `pip install pre-commit && pre-commit run`**
→ The action handles pre-commit environment caching automatically via a built-in
`actions/cache` integration, reducing cold-start time on repeated runs.

**Install openspec globally via `npm install -g openspec` (latest) before pre-commit**
→ The `openspec-validate` hook is `language: system`, meaning it calls whatever
`openspec` is on `PATH`. Installing the latest version is intentional: newer
versions may catch more issues, so CI being stricter than local is desirable, not
a problem.

**Install Python venv deps before pre-commit**
→ The `detector-unit-tests` hook is also `language: system` and requires `flask`
(from `requirements-dev.txt`). Installing into the system Python (not a venv) is
fine in CI — there is no environment isolation concern on a throw-away runner.

**Fork filtering via `github.event.pull_request.head.repo.full_name == github.repository`**
→ Prevents CI from running on PRs from forks, which don't have access to repo
secrets and would fail if any secret-dependent step were added later.

## Risks / Trade-offs

- `language: system` hooks are fragile: if a new system-level hook is added without updating CI setup steps, it will silently fail or error → document in `DEVELOPMENT.md` that any new `language: system` hook needs a corresponding CI setup step
