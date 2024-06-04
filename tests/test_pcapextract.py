import sys
import os
# import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import raatestbed.pcap_extract as pe
# from scapy.all import Radius
# from typing import List, Callable, Tuple
# import logging


class TestPcapExtract:
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

    def test_csid(self, large_download_pcap):
        """Test getting non-vsa (calling_station_id) from packet."""
        packet = large_download_pcap[0]
        calling_station_ids = pe.get_values_for_attribute(packet, 31)
        assert calling_station_ids == [b"B8-27-EB-75-4C-CC"]

    def test_vsa(self, large_download_pcap):
        """Test getting VSA from packet."""
        packet = large_download_pcap[0]
        vsa = pe.get_values_for_attribute(packet, 2, 40808)
        assert vsa == [b"\x02"]

    def test_accept_packets(self, large_download_pcap, large_upload_pcap):
        """Test getting accept packets."""
        up_packet = pe.get_accept_packets(large_upload_pcap)
        down_packet = pe.get_accept_packets(large_download_pcap)
        assert len(up_packet) == 1
        assert len(down_packet) == 1
        assert up_packet[0].authenticator.hex() == "dcf70985877f46bcb341afc6db745676"
        assert down_packet[0].authenticator.hex() == "94947e2d94c8c64fe14796755875d03a"

    def test_start_packets(self, large_download_pcap):
        """Test getting accounting start packets."""
        packets = pe.get_start_packets(large_download_pcap)
        assert len(packets) == 1
        assert packets[0].authenticator.hex() == "fb20183bb2d248aae3296b9cdf724e90"

    def test_update_packets(self, large_download_pcap, large_upload_pcap):
        """Test getting accounting update packets."""
        down_packets = pe.get_update_packets(large_download_pcap)
        up_packets = pe.get_update_packets(large_upload_pcap)
        assert len(down_packets) == 177
        assert len(up_packets) == 214

    def test_stop_packets(self, large_download_pcap):
        """Test getting accounting stop packets."""
        packets = pe.get_stop_packets(large_download_pcap)
        assert len(packets) == 1
        assert packets[0].authenticator.hex() == "176f5639830e4b6be208ca62ac740637"

    def test_total_octets(self, large_download_pcap, large_upload_pcap):
        """Test getting total octetes."""
        down_packets = pe.get_stop_packets(large_download_pcap)
        up_packets = pe.get_stop_packets(large_upload_pcap)
        in_octets = pe.get_total_input_octets(up_packets[0])
        out_octets = pe.get_total_output_octets(down_packets[0])
        assert in_octets == 5682070141
        assert out_octets == 5682218308
