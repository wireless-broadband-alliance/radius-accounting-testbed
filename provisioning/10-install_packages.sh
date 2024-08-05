#!/usr/bin/sh

set -eu

apt update -y
apt install -y ntp cmake gcc python3-dev freeradius tcpdump
