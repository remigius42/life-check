## Purpose
Define the GitHub Actions CI workflow: triggers, pre-commit execution, and setup steps required for `language: system` hooks.

## Requirements

### Requirement: CI runs pre-commit on push to main

The workflow SHALL trigger on every push to `main` in the repository and run all
pre-commit hooks against the changed files.

#### Scenario: Push to main triggers CI

- **WHEN** a commit is pushed to `main`
- **THEN** the `ci` workflow runs and executes all pre-commit hooks

### Requirement: CI runs pre-commit on non-fork PRs

The workflow SHALL trigger on pull requests targeting `main`, but SHALL NOT run on
PRs opened from forks (where the head repo differs from the base repo).

#### Scenario: PR from same repo triggers CI

- **WHEN** a pull request is opened from a branch in the same repository
- **THEN** the `ci` workflow runs and executes all pre-commit hooks

#### Scenario: PR from fork does not trigger CI

- **WHEN** a pull request is opened from a fork
- **THEN** the `ci` workflow does not run

### Requirement: openspec-validate hook runs in CI

The workflow SHALL set a pinned Node.js major version via `actions/setup-node`
before installing the latest `openspec` CLI globally via npm, so the `language:
system` `openspec-validate` hook can resolve the binary under a known runtime.

#### Scenario: openspec binary available during pre-commit

- **WHEN** the CI workflow runs pre-commit
- **THEN** `openspec` is on `PATH` under the configured Node.js version and the `openspec-validate` hook exits successfully

### Requirement: detector-unit-tests hook runs in CI

The workflow SHALL configure Python 3.11 via `actions/setup-python` and install
dependencies from `requirements-dev.txt` before invoking pre-commit, so the
`language: system` `detector-unit-tests` hook can import `flask`.

#### Scenario: Python deps available during pre-commit

- **WHEN** the CI workflow runs pre-commit
- **THEN** `flask` is importable under Python 3.11 and the `detector-unit-tests` hook exits successfully

### Requirement: DEVELOPMENT.md documents CI

`DEVELOPMENT.md` SHALL contain a CI section describing: workflow triggers, the
openspec npm install step and why it is needed, the Python deps install step and
why it is needed, and the fork-filtering behavior.

#### Scenario: Developer can understand CI setup from docs

- **WHEN** a developer reads `DEVELOPMENT.md`
- **THEN** they understand what triggers CI, why openspec and Python deps are
  installed, and that fork PRs are excluded

### Requirement: README.md displays CI status badge

`README.md` SHALL include a GitHub Actions status badge for the `ci` workflow so
the build status is visible at a glance.

#### Scenario: Badge visible in README

- **WHEN** a visitor views the repository on GitHub
- **THEN** a CI status badge is visible in `README.md` linking to the workflow runs
