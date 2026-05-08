## 1. Create docs/ directory and move files

- [x] 1.1 `git mv DEVELOPMENT.md docs/development.md`
- [x] 1.2 `git mv NOTIFICATIONS.md docs/notifications.md`

## 2. Create route docs from README content

- [x] 2.1 Rename `docs/hardware-raspberry-pi.md` → `docs/raspberry-pi.md`; fold in prerequisites, setup steps, Ansible roles
- [x] 2.2 Rename `docs/hardware-esp32.md` → `docs/esp32.md`; fold in prerequisites and ESPHome setup steps

## 3. Rewrite README as thin router

- [x] 3.1 Remove prerequisites, setup, ESPHome setup, and roles sections
- [x] 3.2 Add deployment routes comparison table with links to `docs/raspberry-pi.md` and `docs/esp32.md`
- [x] 3.3 Update `DEVELOPMENT.md` link → `docs/development.md`
- [x] 3.4 Update `NOTIFICATIONS.md` link → `docs/notifications.md`

## 4. Update specs

- [x] 4.1 Sync delta spec: update `openspec/specs/github-actions-ci/spec.md` path reference from `DEVELOPMENT.md` to `docs/development.md`
- [x] 4.2 Update `docs-structure` delta spec to reflect final file names and README-as-router requirement

## 5. Verify

- [x] 5.1 Confirm no remaining references to `DEVELOPMENT.md` or `NOTIFICATIONS.md` at root (grep check)
- [x] 5.2 Run pre-commit to confirm no linting regressions
