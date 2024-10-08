"""Contains default values."""

import os

ROOT_DIR = "/usr/local/raa"
WIRELESS_IFACE = "wlan0"
WIRED_IFACE = "eth0"
CHUNK_SIZE = 1024
SSID = "raatest"
DATA_SERVER_LISTEN_PORT = 8000
DATA_SERVER_PORT = 8000
CHUNKS = 10
SUT = ""
GENERATE_PCAP = True
GENERATE_REPORT = True
UPLOAD_CHUNKS = True
DOWNLOAD_CHUNKS = True
DATA_SERVER_IP = "10.10.10.10"
RELATIVE_PYTEST_INI = os.path.join("raatests", "pytest.ini")
