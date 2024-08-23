# content of conftest.py
import json
import os
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Metadata:
    """Metadata for a test."""

    username: str
    session_duration: int
    chunk_size: str
    chunks: str
    sut_make: str
    sut_model: str
    sut_firmware: str
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
            "sut_make": self.sut_make,
            "sut_model": self.sut_model,
            "sut_firmware": self.sut_firmware,
            "start_time": self.start_time.strftime(self._date_format),
            "end_time": self.end_time.strftime(self._date_format),
        }

    def pretty_print_format(self):
        return json.dumps(self.get_dict(), indent=4)


def get_metadata_dir(root_dir: str) -> str:
    """Return metadata directory."""
    return os.path.join(root_dir, "metadata")


def get_pcap_dir(root_dir: str) -> str:
    """Return pcap directory."""
    return os.path.join(root_dir, "pcap")


def get_reports_dir(root_dir: str) -> str:
    """Return report directory."""
    return os.path.join(root_dir, "reports")


def get_config_dir(root_dir: str) -> str:
    """Return config directory."""
    return os.path.join(root_dir, "config")


def get_logs_dir(root_dir: str) -> str:
    """Return logs directory."""
    return os.path.join(root_dir, "logs")


def get_metadata_filename(test_name, dir) -> str:
    """Return metadata file path for a given test name."""
    return os.path.join(dir, f"{test_name}.metadata.json")


def get_pcap_filename(test_name, dir) -> str:
    """Return pcap file path for a given test name."""
    return os.path.join(dir, f"{test_name}.pcap")


def get_report_filename(test_name, dir) -> str:
    """Return reports file path for a given test name."""
    return os.path.join(dir, f"{test_name}.pdf")


def get_metadata(test_name, root_dir) -> Metadata:
    """Convert metadata JSON file to Metadata object."""
    metadata_dir = get_metadata_dir(root_dir)
    metadata_file = get_metadata_filename(test_name, metadata_dir)
    with open(metadata_file) as f:
        metadata_dict = json.load(f)
    return Metadata(**metadata_dict)
