"""Handles default values and input rules."""

import os
from collections import ChainMap

KEY_ROOT_DIR = "local_output_dir"
KEY_CLIENT_IFACE = "client_iface"
KEY_SERVER_IFACE = "server_iface"
KEY_CHUNK_SIZE = "chunk_size"
KEY_SSID = "ssid"
KEY_DATA_SERVER_LISTEN_PORT = "data_server_listen_port"
KEY_CHUNKS = "chunks"
KEY_GENERATE_PCAP = "generate_pcap"
KEY_GENERATE_REPORT = "generate_report"
KEY_UPLOAD_CHUNKS = "upload_chunks"
KEY_DOWNLOAD_CHUNKS = "download_chunks"
KEY_RELATIVE_PYTEST_INI = "relative_pytest_ini"
KEY_MARKERS = "markers"
KEY_BRAND = "sut_brand"
KEY_HARDWARE = "sut_hardware"
KEY_SOFTWARE = "sut_software"

KEY_DATA_SERVER_IP = "data_server_ip"
KEY_DATA_SERVER_PORT = "data_server_port"
KEY_TEST_NAME = "test_name"

ROOT_DIR = "/usr/local/raa"
CLIENT_IFACE = "wlan0"
SERVER_IFACE = "eth0"
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
MARKERS = "core"
BRAND = "Not Specified"
HARDWARE = "Not Specified"
SOFTWARE = "Not Specified"

def get_required_args() -> list:
  return [KEY_TEST_NAME, KEY_DATA_SERVER_IP, KEY_DATA_SERVER_PORT]

def get_defaults() -> dict:
   """Return the default values. These take lowest priority."""
   defaults = {
     KEY_ROOT_DIR: ROOT_DIR,
     KEY_CLIENT_IFACE: CLIENT_IFACE,
     KEY_SERVER_IFACE: SERVER_IFACE,
     KEY_CHUNK_SIZE: CHUNK_SIZE,
     KEY_SSID: SSID,
     KEY_DATA_SERVER_LISTEN_PORT: DATA_SERVER_LISTEN_PORT,
     KEY_CHUNKS: CHUNKS,
     KEY_GENERATE_PCAP: GENERATE_PCAP,
     KEY_GENERATE_REPORT: GENERATE_REPORT,
     KEY_UPLOAD_CHUNKS: UPLOAD_CHUNKS,
     KEY_DOWNLOAD_CHUNKS: DOWNLOAD_CHUNKS,
     KEY_RELATIVE_PYTEST_INI: RELATIVE_PYTEST_INI,
     KEY_MARKERS: MARKERS,
     KEY_BRAND: BRAND,
     KEY_HARDWARE: HARDWARE,
     KEY_SOFTWARE: SOFTWARE,

   }
   return defaults

def get_all_args(*dicts) -> ChainMap:
    """Merge dictionaries from different optional arguments (e.g., CLI, config, default)."""
    #Raise exception if unknown key is found
    new_dicts = []
    defaults = get_defaults()
    required_args = get_required_args()
    for _dict in dicts:
        #Remove all keys in list required_args from _dict
        for key in required_args:
            if key in _dict.keys():
                _dict.pop(key)
        new_dicts.append(_dict)
    new_dicts.append(defaults)
    return ChainMap(*new_dicts)
