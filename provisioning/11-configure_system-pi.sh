#!/usr/bin/env sh

set -eu

#Disable default wpa_supplicant service (script enables it)
systemctl stop wpa_supplicant

# Configure wlan0
echo """
[Match]
Name=wlan0

[Network]
DHCP=yes
IPv4DefaultRoute=no
IPv6DefaultRoute=no
""" >/etc/systemd/network/10-wlan0.network

# Configure eth0
echo """
[Match]
Name=eth0

[Network]
DHCP=yes
""" >/etc/systemd/network/10-eth0.network

systemctl daemon-reload
systemctl disable --now NetworkManager
systemctl enable --now systemd-networkd
