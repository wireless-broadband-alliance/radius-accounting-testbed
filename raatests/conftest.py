# content of conftest.py
import pytest
import os
import sys
from typing import List
from scapy.all import Radius
from extra_funcs import get_metadata_loc, get_pcap_loc, get_metadata, Metadata

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import raatestbed.pcap_extract as pe


def pytest_addoption(parser):
    parser.addoption(
        "--pcap_dir",
        action="store",
        default="/usr/local/raa/pcap",
        help="Directory to find PCAP and metadata files",
    )
    parser.addoption(
        "--test_name",
        action="store",
        required=True,
        help="Name of test",
    )


def pytest_configure(config):
    """Do preliminary checks to ensure there are PCAP and metadata files before test execution."""
    test_name = config.getoption("--test_name")
    pcap_dir = config.getoption("--pcap_dir")
    config.addinivalue_line("markers", "core: basic tests")
    config.addinivalue_line("markers", "core_upload: basic tests for upload")
    config.addinivalue_line("markers", "core_download: basic tests for download")
    config.addinivalue_line("markers", "openroaming: openroaming tests")
    # These functions will raise errors if the files are not found
    _ = get_metadata_loc(test_name, pcap_dir)
    _ = get_pcap_loc(test_name, pcap_dir)


@pytest.fixture
def metadata(request) -> Metadata:
    """Return metadata for a given test name."""
    test_name = request.config.getoption("--test_name")
    directory = request.config.getoption("--pcap_dir")
    return get_metadata(test_name, directory)


@pytest.fixture
def packets(request) -> List[Radius]:
    """Return relevant packets from PCAP file."""
    test_name = request.config.getoption("--test_name")
    directory = request.config.getoption("--pcap_dir")
    metadata = get_metadata(test_name, directory)
    username = metadata.username
    pcap_loc = get_pcap_loc(test_name, directory)
    pcap = pe.get_relevant_packets(pcap_loc, username)
    return pcap
