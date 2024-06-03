import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import raatestbed.pcap_extract as pe
# from scapy.all import Radius
# from typing import List, Callable, Tuple
# import logging


class TestBasic:
    def test_read_pcap_download(self, large_download_pcap):
        """Test packet count."""
        assert len(large_download_pcap) == 388

    def test_read_pcap_upload(self, large_upload_pcap):
        """Test packet count."""
        assert len(large_upload_pcap) == 462

    def test_filter_pcap_by_username(
        self, large_download_pcap, large_download_username, large_upload_username
    ):
        """Test filtering packets by username."""
        # Download username in download packets
        packets = pe.get_packets_by_username(
            large_download_pcap, large_download_username
        )
        assert len(packets) == 187
        # Upload username not in download packets
        packets = pe.get_packets_by_username(large_download_pcap, large_upload_username)
        assert len(packets) == 0

    def test_get_latest_packet(self, large_download_pcap):
        """Test getting the latest packet."""
        packet = pe.get_latest_radius_packet(large_download_pcap)
        assert packet.authenticator.hex() == "300eb278f27848846407052459ae166f"
