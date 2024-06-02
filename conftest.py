# content of conftest.py
import pytest
import raatestbed.pcap_extract as pe
import os
import json
from typing import Tuple, List
from glob import glob
from scapy.all import Radius

from dataclasses import asdict, dataclass


@dataclass
class Metadata:
    """Metadata for a test."""

    username: str
    session_duration: str
    chunk_size: str
    chunks: str


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


def get_metadata_loc(test_name, pcap_dir) -> str:
    """Return metadata file path for a given test name."""
    metadata = glob(os.path.join(pcap_dir, f"{test_name}*.metadata.json"))
    # Check if there is exactly one PCAP and one metadata file, raise error otherwise
    if len(metadata) != 1:
        metadata_str = ", ".join(metadata)
        raise ValueError(
            f"Incorrect number of metadata files found....metadata: {metadata_str}"
        )
    return metadata[0]


def get_pcap_loc(test_name, pcap_dir) -> str:
    """Return PCAP file path for a given test name."""
    pcaps = glob(os.path.join(pcap_dir, f"{test_name}*.pcap"))
    # Check if there is exactly one PCAP and one metadata file, raise error otherwise
    if len(pcaps) != 1:
        pcaps_str = ", ".join(pcaps)
        raise ValueError(f"Incorrect number of PCAP files found....PCAPs: {pcaps_str}")
    return pcaps[0]


def get_metadata(test_name, pcap_dir) -> Metadata:
    metadata_loc = get_metadata_loc(test_name, pcap_dir)
    with open(metadata_loc) as f:
        metadata_dict = json.load(f)
    return Metadata(**metadata_dict)


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
