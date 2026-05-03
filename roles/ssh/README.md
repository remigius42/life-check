# ssh

Hardens the SSH daemon on Debian-based systems.

## What it does

**Always** (unconditional):

- Sets `PermitRootLogin no` in `/etc/ssh/sshd_config`
- Sets `PubkeyAuthentication yes` in `/etc/ssh/sshd_config`
- Restarts sshd on any config change

**When `ssh_manage_keys: true`** (default):

- Asserts `~/.ssh/authorized_keys` is non-empty on the target (lockout prevention)
- Deploys the operator's public key from `ssh_public_key_file` (control node path)
- Sets `PasswordAuthentication no` in `/etc/ssh/sshd_config`

## Variables

| Variable               | Default                    | Description                                                                                        |
| ---------------------- | -------------------------- | -------------------------------------------------------------------------------------------------- |
| `ssh_manage_keys`      | `true`                     | Gate key deployment and `PasswordAuthentication no`. Set `false` when control node has no SSH key. |
| `ssh_public_key_file`  | `~/.ssh/id_ed25519.pub`    | Path to the public key on the **control node** (read via `lookup('file', ...)`).                   |
| `ssh_service_name`     | auto                       | `ssh` on Debian/Ubuntu, `sshd` on RHEL/Fedora.                                                     |
| `ssh_remote_user_home` | `/home/{{ ansible_user }}` | Home directory of the remote `ansible_user`.                                                       |

## Usage modes

### Key-capable control node (`ssh_manage_keys: true`)

```yaml
# group_vars/all/vars.yml
ssh_manage_keys: true
ssh_public_key_file: "~/.ssh/id_ed25519.pub"
```

### No key on control node (`ssh_manage_keys: false`)

```yaml
# group_vars/all/vars.yml
ssh_manage_keys: false
```

Unconditional hardening (`PermitRootLogin no`, `PubkeyAuthentication yes`) still applies.
`PasswordAuthentication` is left unchanged — deploy fail2ban to mitigate brute-force risk.
