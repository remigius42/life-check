## 1. Locales role

- [x] 1.1 Create `roles/locales/tasks/main.yml` from `notes/role-tasks.yml`
- [x] 1.2 Create `roles/locales/defaults/main.yml` from `notes/role-defaults.yml`
- [x] 1.3 Create `roles/locales/handlers/main.yml` from `notes/role-handlers.yml`
- [x] 1.4 Create `roles/locales/meta/main.yml` from `notes/role-meta.yml`
- [x] 1.5 Create `roles/locales/README.md`
- [x] 1.6 Create `roles/locales/tests/test.yml`

## 2. Group vars

- [x] 2.1 Create `group_vars/all/vars.yml` from `notes/group-vars.yml`

## 3. Playbooks

- [x] 3.1 Create `playbooks/site.yml` with `vars_files` + `locales` role
- [x] 3.2 Create `playbooks/verify.yml` asserting package, locales in locale.gen, and timezone
