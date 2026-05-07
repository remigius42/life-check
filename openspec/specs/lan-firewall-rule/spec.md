## Purpose
Define the UFW firewall rule added by the `detector` Ansible role to allow LAN access to the beam-detector web UI port.

## Requirements

### Requirement: UFW rule allows LAN access to web port
The `detector` Ansible role SHALL add a UFW rule allowing TCP traffic on `{{ detector_web_port }}` from `{{ ufw_lan_subnet }}` only. The rule SHALL use `community.general.ufw` consistent with the existing `ufw` role convention.

#### Scenario: LAN access allowed after role run
- **WHEN** the role is applied
- **THEN** a UFW rule exists permitting TCP on `detector_web_port` from `ufw_lan_subnet`

#### Scenario: Non-LAN traffic blocked
**Prerequisite:** the `ufw` role has been applied and its default deny-incoming policy is in effect.
- **WHEN** a request arrives from outside `ufw_lan_subnet` on `detector_web_port`
- **THEN** UFW blocks it (this is an integration scenario requiring both the `ufw` role and the `detector` role to be applied)

### Requirement: UFW rule scoped to LAN subnet variable
The firewall rule SHALL reference `ufw_lan_subnet` (defined by the `ufw` role in `group_vars/all/vars.yml`) rather than hardcoding a subnet. This ensures the web server port follows the same LAN boundary as SSH.

#### Scenario: Subnet variable drives the rule
- **WHEN** `ufw_lan_subnet` is set to `192.168.1.0/24`
- **THEN** the UFW rule source is `192.168.1.0/24`
