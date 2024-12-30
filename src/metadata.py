"""Contains metadata-related imports."""

import json
from datetime import datetime
from dataclasses import dataclass
from files import get_metadata_filename
from data_transfer import UsageCounter
from typing import Union


@dataclass
class Metadata:
    """Metadata for a test."""

    username: str
    session_duration: int
    chunk_size: str
    chunks: str
    sut_brand: str
    sut_hardware: str
    sut_software: str
    start_time: datetime
    end_time: datetime
    uploaded: bool
    downloaded: bool
    usage_upload: Union[UsageCounter, None] = None
    usage_download: Union[UsageCounter, None] = None
    _date_format: str = "%Y-%m-%d %H:%M:%S"

    def __post_init__(self):
        # Convert start_time and end_time to datetime if imported as string
        if isinstance(self.start_time, str):
            self.start_time = datetime.strptime(self.start_time, self._date_format)
        if isinstance(self.end_time, str):
            self.end_time = datetime.strptime(self.end_time, self._date_format)

    def get_upload_packets(self):
        return self.usage_upload.packets_sent if self.usage_upload else None

    def get_download_packets(self):
        return self.usage_download.packets_recv if self.usage_download else None

    def get_dict(self) -> dict:
        return {
            "username": self.username,
            "session_duration": self.session_duration,
            "chunk_size": self.chunk_size,
            "chunks": self.chunks,
            "sut_brand": self.sut_brand,
            "sut_hardware": self.sut_hardware,
            "sut_software": self.sut_software,
            "uploaded": self.uploaded,
            "usage_upload": self.usage_upload.to_dict() if self.usage_upload else None,
            "downloaded": self.downloaded,
            "usage_download": self.usage_download.to_dict()
            if self.usage_download
            else None,
            "start_time": self.start_time.strftime(self._date_format),
            "end_time": self.end_time.strftime(self._date_format),
        }

    def pretty_print_format(self):
        return json.dumps(self.get_dict(), indent=4)


def get_metadata(test_name, root_dir) -> Metadata:
    """Convert metadata JSON file to Metadata object."""
    metadata_file = get_metadata_filename(test_name, root_dir)
    with open(metadata_file) as f:
        metadata_dict = json.load(f)
    metadata_dict["usage_upload"] = (
        UsageCounter(**metadata_dict["usage_upload"])
        if metadata_dict["usage_upload"]
        else None
    )
    metadata_dict["usage_download"] = (
        UsageCounter(**metadata_dict["usage_download"])
        if metadata_dict["usage_download"]
        else None
    )
    return Metadata(**metadata_dict)
