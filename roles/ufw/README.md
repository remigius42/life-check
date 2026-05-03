# ufw

Deny-all inbound firewall with SSH from LAN allowed, via UFW.

## Variables

| Variable         | Default | Description                                                    |
| ---------------- | ------- | -------------------------------------------------------------- |
| `ufw_lan_subnet` | `""`    | IPv4 CIDR for the LAN subnet (required, e.g. `192.168.0.0/24`) |

`ufw_lan_subnet` has no usable default — set it explicitly in `group_vars`.

## What it does

1. Asserts `ufw_lan_subnet` is a valid IPv4 CIDR before touching firewall state
1. Installs `ufw`
1. Default policy: deny incoming, allow outgoing
1. Allows TCP port 22 from `ufw_lan_subnet`
1. Enables UFW (active at boot)

## Requirements

`community.general` collection (already in `collections/requirements.yml`).
