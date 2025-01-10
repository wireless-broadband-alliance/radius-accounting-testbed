"""Contains default values. This file contains single source of truth for possible input values."""

import os
from collections import ChainMap

KEY_ROOT_DIR = "ROOT_DIR"
KEY_WIRELESS_IFACE = "WIRELESS_IFACE"
KEY_WIRED_IFACE = "WIRED_IFACE"
KEY_CHUNK_SIZE = "CHUNK_SIZE"
KEY_SSID = "SSID"
KEY_DATA_SERVER_LISTEN_PORT = "DATA_SERVER_LISTEN_PORT"
KEY_DATA_SERVER_PORT = "DATA_SERVER_PORT"
KEY_CHUNKS = "CHUNKS"
KEY_SUT = "SUT"
KEY_GENERATE_PCAP = "GENERATE_PCAP"
KEY_GENERATE_REPORT = "GENERATE_REPORT"
KEY_UPLOAD_CHUNKS = "UPLOAD_CHUNKS"
KEY_DOWNLOAD_CHUNKS = "DOWNLOAD_CHUNKS"
KEY_DATA_SERVER_IP = "DATA_SERVER_IP"
KEY_RELATIVE_PYTEST_INI = "RELATIVE_PYTEST_INI"

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

def get_defaults() -> dict:
   """Return the default values. These take lowest priority."""
   defaults = {
     KEY_ROOT_DIR: ROOT_DIR,
     KEY_WIRELESS_IFACE: WIRELESS_IFACE,
     KEY_WIRED_IFACE: WIRED_IFACE,
     KEY_CHUNK_SIZE: CHUNK_SIZE,
     KEY_SSID: SSID,
     KEY_DATA_SERVER_LISTEN_PORT: DATA_SERVER_LISTEN_PORT,
     KEY_DATA_SERVER_PORT: DATA_SERVER_PORT,
     KEY_CHUNKS: CHUNKS,
     KEY_SUT: SUT,
     KEY_GENERATE_PCAP: GENERATE_PCAP,
     KEY_GENERATE_REPORT: GENERATE_REPORT,
     KEY_UPLOAD_CHUNKS: UPLOAD_CHUNKS,
     KEY_DOWNLOAD_CHUNKS: DOWNLOAD_CHUNKS,
     KEY_DATA_SERVER_IP: DATA_SERVER_IP,
     KEY_RELATIVE_PYTEST_INI: RELATIVE_PYTEST_INI,
   }
   return defaults

def get_all_args(*dicts) -> ChainMap:
    """Merge dictionaries from different arguments (e.g., CLI, config, default)."""
    #Raise exception if unknown key is found
    new_dicts = []
    defaults = get_defaults()
    for _dict in dicts:
        for key in _dict.keys():
            if key not in defaults.keys():
                raise KeyError(f"Unknown key {key} found in dictionary {_dict}")
        new_dicts.append(_dict)
    new_dicts.append(defaults)
    return ChainMap(*new_dicts)
