# content of conftest.py
import pytest
import os
import json
import sys
from typing import List
from glob import glob
from scapy.all import Radius
from dataclasses import dataclass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import raatestbed.pcap_extract as pe


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


def __check_for_one_file(glob_pattern: str, file_type: str) -> str:
    """Raise error if incorrect number of files found for a given test name."""
    files = glob(glob_pattern)
    # Check if there is exactly one metadata file, raise error otherwise
    if len(files) == 0:
        raise ValueError(f"No {file_type} file found, glob pattern: {glob_pattern}")
    if len(files) != 1:
        files_str = ", ".join(files)
        raise ValueError(
            f"More than one metadata file matches glob pattern {glob_pattern}: {files_str}"
        )
    assert len(files) == 1
    return files[0]


def get_metadata_loc(test_name, pcap_dir) -> str:
    """Return metadata file path for a given test name."""
    glob_pattern = os.path.join(pcap_dir, f"{test_name}*.metadata.json")
    return __check_for_one_file(glob_pattern, "metadata")


def get_pcap_loc(test_name, pcap_dir) -> str:
    """Return PCAP file path for a given test name."""
    glob_pattern = os.path.join(pcap_dir, f"{test_name}*.pcap")
    return __check_for_one_file(glob_pattern, "PCAP")


def pytest_configure(config):
    """Do preliminary checks to ensure there are PCAP and metadata files before test execution."""
    test_name = config.getoption("--test_name")
    pcap_dir = config.getoption("--pcap_dir")
    # These functions will raise errors if the files are not found
    _ = get_metadata_loc(test_name, pcap_dir)
    _ = get_pcap_loc(test_name, pcap_dir)


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
