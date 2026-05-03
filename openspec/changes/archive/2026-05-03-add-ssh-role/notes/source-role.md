# Reference: SSH Role Implementation

Reference implementation for the ssh role. Use these as the basis for the new role files.

## defaults/main.yml

```yaml
# SPDX-License-Identifier: MIT
---
# Set false when control node has no SSH key (e.g. Windows/TeamViewer).
# Skips pre-check, key deployment, and PasswordAuthentication enforcement.
ssh_manage_keys: true

# Path to the public key file on the CONTROL NODE (read via lookup('file', ...))
ssh_public_key_file: "~/.ssh/id_ed25519.pub"

# Service name differs by distro: "ssh" on Debian/Ubuntu, "sshd" on RHEL/Fedora
ssh_service_name: "{{ 'ssh' if ansible_facts['os_family'] == 'Debian' else 'sshd' }}"

# Explicit home directory of the remote ansible_user (avoids tilde ambiguity under become)
ssh_remote_user_home: "/home/{{ ansible_user }}"
```

## tasks/main.yml

Task order: unconditional hardening runs first so those settings apply even if the pre-check aborts the play.

```yaml
# SPDX-License-Identifier: MIT
---
# Unconditional hardening — runs before key-management checks
- name: Harden sshd_config (key-independent settings)
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: "{{ item.regexp }}"
    line: "{{ item.line }}"
    state: present
    validate: /usr/sbin/sshd -t -f %s
  loop:
    - { regexp: '^\s*#?\s*PermitRootLogin',      line: 'PermitRootLogin no' }
    - { regexp: '^\s*#?\s*PubkeyAuthentication', line: 'PubkeyAuthentication yes' }
  become: true
  notify: Restart sshd

# Key management block — only when ssh_manage_keys: true
- name: Key management
  when: ssh_manage_keys
  block:
    - name: Check authorized_keys exists and is non-empty
      ansible.builtin.stat:
        path: "{{ ssh_remote_user_home }}/.ssh/authorized_keys"
      register: ssh_authorized_keys

    - name: Abort if no SSH key deployed
      ansible.builtin.assert:
        that:
          - ssh_authorized_keys.stat.exists
          - ssh_authorized_keys.stat.size > 0
        fail_msg: >
          {{ ssh_remote_user_home }}/.ssh/authorized_keys is absent or empty on {{ inventory_hostname }}.
          Deploy an SSH public key before running this role to avoid lockout.

    - name: Deploy public key
      ansible.posix.authorized_key:
        user: "{{ ansible_user }}"
        state: present
        key: "{{ lookup('file', ssh_public_key_file) }}"

    - name: Disable password authentication
      ansible.builtin.lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^\s*#?\s*PasswordAuthentication'
        line: 'PasswordAuthentication no'
        state: present
        validate: /usr/sbin/sshd -t -f %s
      become: true
      notify: Restart sshd
```

## handlers/main.yml

```yaml
# SPDX-License-Identifier: MIT
---
- name: Restart sshd
  ansible.builtin.service:
    name: "{{ ssh_service_name }}"
    state: restarted
  become: true
```

## Collections requirement

`ansible.posix` is required for `ansible.posix.authorized_key`. Verify it is listed in `collections/requirements.yml`. If not, add:

```yaml
- name: ansible.posix
```

## Conventions from roles/locales (apply to new role)

- `become: true` on each task that touches system files (not at play level)
- All variables prefixed with role name (`ssh_`)
- Remove unused role directories (`templates/`, `vars/`, `tests/`)
- `meta/main.yml` structure: author `Andreas Remigius Schmidt`, company `binary poetry gmbh`, license `MIT`, `min_ansible_version: "2.14"`
- `# SPDX-License-Identifier: MIT` header on every YAML file
