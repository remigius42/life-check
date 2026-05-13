#!/bin/bash
# cspell:ignore cmdline firstrun mgmt nmconnection nonint raspi rfkill trixie
exec > /var/log/firstrun.log 2>&1
set -euxo pipefail

readonly HOSTNAME="life-check"       # ← change; SSH via <hostname>.local (mDNS)
readonly PI_USER="pi"                # ← change
readonly PI_PASSWORD="YourPassword"  # ← change (same security caveats as WIFI_PSK)
readonly WIFI_SSID="YourSSID"        # ← change
readonly WIFI_PSK="YourWifiPassword" # ← change
readonly WIFI_COUNTRY="CH"           # ← change (ISO 3166-1 alpha-2)
readonly BOOT=/boot/firmware

# hostnamectl requires dbus which is not up at this early boot stage
echo "$HOSTNAME" > /etc/hostname
sed -i "s/127\.0\.1\.1.*/127.0.1.1\t$HOSTNAME/" /etc/hosts

# Trixie pre-creates pi with /usr/sbin/nologin; other usernames need useradd
# No PAM complexity checks apply when run as root
# gpio/i2c/spi groups exist on stock RPi OS but are created late — skip gracefully if missing
if id "$PI_USER" &>/dev/null; then
    usermod -s /bin/bash "$PI_USER"
else
    useradd -m -s /bin/bash "$PI_USER"
fi
usermod -aG sudo "$PI_USER"
usermod -aG gpio,i2c,spi "$PI_USER" 2>/dev/null || true
echo "$PI_USER:$PI_PASSWORD" | chpasswd

rfkill unblock wifi
raspi-config nonint do_wifi_country "$WIFI_COUNTRY"

UUID=$(cat /proc/sys/kernel/random/uuid)
mkdir -p /etc/NetworkManager/system-connections
cat > /etc/NetworkManager/system-connections/preconfigured.nmconnection <<EOF
[connection]
id=${WIFI_SSID}
uuid=${UUID}
type=wifi

[wifi]
mode=infrastructure
ssid=${WIFI_SSID}

[wifi-security]
auth-alg=open
key-mgmt=wpa-psk
psk=${WIFI_PSK}

[ipv4]
method=auto

[ipv6]
# UFW only allowlists IPv4; disable IPv6 to keep network config consistent
method=disabled
EOF
chmod 600 /etc/NetworkManager/system-connections/preconfigured.nmconnection

systemctl enable --now ssh

sed -i 's| systemd\.run=[^ ]*||g; s| systemd\.run_success_action=[^ ]*||g; s| systemd\.run_failure_action=[^ ]*||g; s| systemd\.unit=[^ ]*||g' "$BOOT/cmdline.txt"
# shred is ineffective on SD cards (wear-leveling); the password also persists in plaintext in
# /etc/NetworkManager/system-connections/ on the root fs regardless
rm -f "$BOOT/firstrun.sh"
# log only removed on success; if it persists, check /var/log/firstrun.log for the failure
rm -f /var/log/firstrun.log
