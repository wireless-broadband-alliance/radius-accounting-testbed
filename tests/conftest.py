import pytest
import sys
import os
from scapy.all import Radius
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import src.pcap_extract as pe


PCAPDIR = "tests/data/pcaps"


@pytest.fixture
def large_download_pcap() -> List[Radius]:
    # Read download PCAP file
    large_download_pcap_file = "test_dl_5gb.tcpdump.radius.pcap"
    file = os.path.join(PCAPDIR, large_download_pcap_file)
    return pe.get_radius_packets(file)


@pytest.fixture
def large_upload_pcap() -> List[Radius]:
    # Read download PCAP file
    large_download_pcap_file = "test_ul_5gb.tcpdump.radius.pcap"
    file = os.path.join(PCAPDIR, large_download_pcap_file)
    return pe.get_radius_packets(file)


@pytest.fixture
def large_download_octets():
    return 5 * 1024 * 1024 * 1024


@pytest.fixture
def large_upload_duration():
    return 2375


@pytest.fixture
def large_upload_octets():
    return 5 * 1024 * 1024 * 1024


@pytest.fixture
def large_download_duration():
    return 1773


@pytest.fixture
def large_download_username():
    return "1542aeee-0c55-404c-badf-ccc5093d10ca@example.com"


@pytest.fixture
def large_upload_username():
    return "e73d671e-e0b7-4000-9ca6-196a390585d3@example.com"
