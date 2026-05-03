## Purpose
Deny-all inbound firewall with SSH from LAN subnet allowed, via UFW.

## Requirements

### Requirement: ufw_lan_subnet validated before rule application
The role SHALL assert that `ufw_lan_subnet` is defined, non-empty, and matches a valid IPv4 CIDR pattern before applying any firewall rules.

#### Scenario: Invalid or empty subnet
- **WHEN** `ufw_lan_subnet` is empty or not a valid CIDR
- **THEN** the role fails with a descriptive message before modifying any firewall rules

#### Scenario: Valid subnet
- **WHEN** `ufw_lan_subnet` is a valid CIDR (e.g. `192.168.0.0/24`)
- **THEN** the role proceeds with rule application

### Requirement: Default deny incoming
The role SHALL set the default inbound policy to `deny`.

#### Scenario: Default policy applied
- **WHEN** the role runs
- **THEN** all inbound traffic not explicitly allowed is denied

### Requirement: Default allow outgoing
The role SHALL set the default outbound policy to `allow`.

#### Scenario: Default outgoing policy applied
- **WHEN** the role runs
- **THEN** all outbound traffic is allowed

### Requirement: SSH allowed from LAN subnet
The role SHALL allow TCP port 22 from `{{ ufw_lan_subnet }}` only.

#### Scenario: SSH from LAN subnet
- **WHEN** a connection to port 22 originates from `ufw_lan_subnet`
- **THEN** the connection is allowed

#### Scenario: SSH from outside LAN subnet
- **WHEN** a connection to port 22 originates from outside `ufw_lan_subnet`
- **THEN** the connection is denied

### Requirement: UFW enabled and active
The role SHALL enable UFW so it is active and starts on boot.

#### Scenario: UFW enabled
- **WHEN** the role completes
- **THEN** `ufw status` reports `Status: active`
