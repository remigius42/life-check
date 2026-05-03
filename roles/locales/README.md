# locales

Installs the `locales` package, enables specified locales in `/etc/locale.gen`, and sets the system timezone via `timedatectl`.

## Requirements

- Debian-based OS (Raspberry Pi OS)
- systemd (`timedatectl`)

## Role Variables

| Variable                  | Default                      | Description        |
| ------------------------- | ---------------------------- | ------------------ |
| `locales_locale_gen_path` | `/etc/locale.gen`            | Path to locale.gen |
| `locales_timezone`        | `UTC`                        | System timezone    |
| `locales_locales`         | `de_CH.UTF-8`, `en_US.UTF-8` | Locales to enable  |

## Example Playbook

```yaml
- hosts: all
  roles:
    - locales
```
