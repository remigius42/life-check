## MODIFIED Requirements

### Requirement: docs/development.md documents CI

`docs/development.md` SHALL contain a CI section describing: workflow triggers,
the openspec npm install step and why it is needed, the Python deps install step
and why it is needed, and the fork-filtering behavior.

#### Scenario: Developer can understand CI setup from docs

- **WHEN** a developer reads `docs/development.md`
- **THEN** they understand what triggers CI, why openspec and Python deps are
  installed, and that fork PRs are excluded
