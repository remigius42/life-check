## Why

The repo has no automated checks; errors only surface locally via pre-commit. A CI
workflow catches issues on every push and PR before they reach `main`.

## What Changes

- Add `.github/workflows/ci.yml` — runs pre-commit on push and non-fork PRs to `main`
- Install `openspec` globally via npm before pre-commit (required for the `language: system` `openspec-validate` hook)
- Update `DEVELOPMENT.md` to document CI triggers, the openspec install step, and fork-filtering behavior
- Add CI status badge to `README.md`

## Capabilities

### New Capabilities

- `github-actions-ci`: GitHub Actions workflow that gates pushes and PRs with pre-commit checks

### Modified Capabilities

## Impact

- New file: `.github/workflows/ci.yml`
- Modified files: `DEVELOPMENT.md`, `README.md`
- No runtime or Ansible changes
