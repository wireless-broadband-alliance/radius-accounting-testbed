# content of conftest.py
import json
import os
from datetime import datetime
from glob import glob
from dataclasses import dataclass


@dataclass
class Metadata:
    """Metadata for a test."""

    username: str
    session_duration: int
    chunk_size: str
    chunks: str
    start_time: datetime
    end_time: datetime
    _date_format: str = "%Y-%m-%d %H:%M:%S"

    def __post_init__(self):
        # Convert start_time and end_time to datetime if imported as string
        if isinstance(self.start_time, str):
            self.start_time = datetime.strptime(self.start_time, self._date_format)
        if isinstance(self.end_time, str):
            self.end_time = datetime.strptime(self.end_time, self._date_format)

    def get_dict(self) -> dict:
        return {
            "username": self.username,
            "session_duration": self.session_duration,
            "chunk_size": self.chunk_size,
            "chunks": self.chunks,
            "start_time": self.start_time.strftime(self._date_format),
            "end_time": self.end_time.strftime(self._date_format),
        }

    def pretty_print_format(self):
        return json.dumps(self.get_dict(), indent=4)


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
    glob_pattern = os.path.join(pcap_dir, f"{test_name}*.metadata.json")
    """Return metadata file path for a given test name."""
    return __check_for_one_file(glob_pattern, "metadata")


def get_pcap_loc(test_name, pcap_dir) -> str:
    """Return PCAP file path for a given test name."""
    glob_pattern = os.path.join(pcap_dir, f"{test_name}*.pcap")
    return __check_for_one_file(glob_pattern, "PCAP")


def get_metadata(test_name, pcap_dir) -> Metadata:
    """Convert metadata JSON file to Metadata object."""
    metadata_loc = get_metadata_loc(test_name, pcap_dir)
    with open(metadata_loc) as f:
        metadata_dict = json.load(f)
    return Metadata(**metadata_dict)
