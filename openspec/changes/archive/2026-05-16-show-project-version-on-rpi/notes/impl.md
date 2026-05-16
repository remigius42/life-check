# Implementation Notes

## Ansible lookup

Use `git describe --tags` (not bare `git describe`). `--tags` includes lightweight
tags, so the `initial` lightweight tag at the first commit guarantees resolution
always succeeds — no fallback needed.

```yaml
- name: Capture project version
  ansible.builtin.set_fact:
    detector_version: "{{ lookup('pipe', 'git describe --tags') }}"
```

## Where to put the set_fact

Add it to `roles/detector/tasks/main.yml` (not the playbook), so the version is
captured whenever the role runs, not just in the full site play.

## Existing pattern to follow in the service template

`roles/detector/templates/beam-detector-web.service.j2` line 17 already has:

```
Environment=DETECTOR_PICO_CSS="pico-{{ detector_pico_version }}.min.css"
```

Add `DETECTOR_VERSION` on the next line using the same form.
