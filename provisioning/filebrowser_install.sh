#!/usr/bin/sh

set -eu
CONFIG_DIR=/etc/filebrowser
SERVICE_FILE="/etc/systemd/system/filebrowser@.service"

echo "Installing filebrowser"
rm -rf $CONFIG_DIR
mkdir -p $CONFIG_DIR
cd $CONFIG_DIR
curl -fsSL https://raw.githubusercontent.com/filebrowser/get/master/get.sh | bash

echo "Creating Systemd service file $SERVICE_FILE"
echo """
[Unit]
Description=File Browser Service for %I
After=network.target

[Service]
Type=simple
Restart=on-failure
RestartSec=5s
ExecStart=filebrowser -r %I --noauth --address 0.0.0.0

[Install]
WantedBy=multi-user.target
""" >$SERVICE_FILE

systemctl daemon-reload
systemctl start filebrowser@-usr-local-raa
