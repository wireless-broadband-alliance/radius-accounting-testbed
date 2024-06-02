# content of conftest.py
import pytest
import raatestbed.pcap_extract as pe
import os
import json
from typing import Tuple, List
from glob import glob
from scapy.all import Radius


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


def get_pcap_and_metadata(test_name, pcap_dir) -> Tuple[str, str]:
    """Return PCAP and metadata files for a given test name."""
    pcaps = glob(os.path.join(pcap_dir, f"{test_name}*.pcap"))
    metadata = glob(os.path.join(pcap_dir, f"{test_name}*.metadata.json"))
    # Check if there is exactly one PCAP and one metadata file, raise error otherwise
    if len(pcaps) != 1 or len(metadata) != 1:
        pcaps_str = ", ".join(pcaps)
        metadata_str = ", ".join(metadata)
        raise ValueError(
            f"Incorrect number of PCAPs or metadata files found....pcaps: {pcaps_str}, metadata: {metadata_str}"
        )
    return pcaps[0], metadata[0]


@pytest.fixture
def testdata(request) -> Tuple[List[Radius], dict]:

@pytest.fixture
def testdata(request) -> Tuple[List[Radius], dict]:
    test_name = request.config.getoption("--test_name")
    directory = request.config.getoption("--pcap_dir")
    pcap_loc, metadata_loc = get_pcap_and_metadata(test_name, directory)
    with open(metadata_loc) as f:
        metadata = json.load(f)
    username = metadata["username"]
    pcap = pe.get_relevant_packets(pcap_loc, username)
    return pcap, metadata
