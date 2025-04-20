#!/usr/bin/env sh

set -eu

apt update -y
apt install -y ntp cmake gcc python3-dev python3-venv freeradius tcpdump wpasupplicant
