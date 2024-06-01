import raatestbed.pcap_extract as pe
from scapy.all import Radius
from typing import List, Callable, Tuple
import logging
import pytest
from glob import glob
import os
# from IPython import embed


# TODO: Change fixtures to dynamically set username, input_pcap, download/upload octets
# TODO: Possibly change test library
# TODO: Use more verbose logging so we can use logger


@pytest.fixture
def large_download_pcap() -> List[Radius]:
    """Import PCAP from large file download and provide to test functions."""
    username = "1542aeee-0c55-404c-badf-ccc5093d10ca@example.com"
    input_pcap = "pcaps/test_dl_5gb.tcpdump.radius.pcap"
    return pe.get_relevant_packets(input_pcap, username)


@pytest.fixture
def large_upload_pcap() -> List[Radius]:
    """Import PCAP from large file upload and provide to test functions."""
    username = "e73d671e-e0b7-4000-9ca6-196a390585d3@example.com"
    input_pcap = "pcaps/test_ul_5gb.tcpdump.radius.pcap"
    return pe.get_relevant_packets(input_pcap, username)


@pytest.fixture
def large_download_octets() -> int:
    return 5 * 1024 * 1024 * 1024


@pytest.fixture
def large_upload_octets() -> int:
    return 5 * 1024 * 1024 * 1024


@pytest.fixture
def large_upload_duration() -> int:
    return 2375


@pytest.fixture
def large_download_duration() -> int:
    return 1773


class TestAttributeChecks:
    def test_unique_persistent_acct_session_id(self, large_download_pcap):
        """Unique and persistent Acct-Session-Id in accounting sessions."""
        # Get all Acct-Session-Id values from the packets, then check if there is only one unique value.
        packets = large_download_pcap
        acct_session_ids = []
        acct_req_packets = pe.get_packets_by_codes(packets, 4)
        for acct_packet in acct_req_packets:
            acct_session_ids += pe.get_acct_session_id(acct_packet)
        # Each packet has an Acct-Session-Id
        assert len(acct_req_packets) == len(acct_session_ids)
        # Account-Session-Id is unique
        assert len(set(acct_session_ids)) == 1
        session_id = acct_session_ids[0]
        # Account-Session-Id looks unique
        assert len(session_id) > 5

    def test_acct_session_id_auth_acct(self, large_download_pcap):
        """Acct-Session-Id is persistent in authentication and accounting sessions."""
        packets = large_download_pcap
        acct_session_ids = []
        req_packets = pe.get_packets_by_codes(packets, 1, 4)
        for packet in req_packets:
            acct_session_ids += pe.get_acct_session_id(packet)
        # Each packet has an Acct-Session-Id
        assert len(req_packets) == len(acct_session_ids)

    def test_start_update_stop_present(self, large_download_pcap: List[Radius]):
        """Start, Update, and Stop records are present in accounting session."""
        packets = large_download_pcap
        start_packets = pe.get_start_packets(packets)
        update_packets = pe.get_update_packets(packets)
        stop_packets = pe.get_stop_packets(packets)

        assert len(stop_packets) == 1
        assert len(start_packets) == 1
        assert len(update_packets) >= 0

    def test_stop_record_last_message(self, large_download_pcap):
        """Stop record is last message in accounting session."""
        packets = large_download_pcap
        latest_packet = pe.get_latest_radius_packet(packets)
        latest_packet_acct_status_type = pe.get_values_for_attribute(latest_packet, 40)
        # Only one Acct-Status-Type field
        assert len(latest_packet_acct_status_type) == 1
        # Acct-Status-Type is Stop (2)
        assert latest_packet_acct_status_type[0] == 2

    def test_stop_record_highest_usage(self, large_download_pcap: List[Radius]):
        """Stop record contains highest usage fields."""
        packets = large_download_pcap
        stop_packets = pe.get_stop_packets(packets)
        update_packets = pe.get_update_packets(packets)
        packets = update_packets + stop_packets
        # Only one Stop packet
        assert len(stop_packets) == 1

        stop_packet = stop_packets[0]
        # Get all totals for input and output octets (tonnage) for each packet
        all_input_octets = []
        all_output_octets = []
        for packet in packets:
            all_input_octets.append(pe.get_total_input_octets(packet))
            all_output_octets.append(pe.get_total_output_octets(packet))
        # Max values in each list should be in the Stop packet
        assert max(all_input_octets) == pe.get_total_input_octets(stop_packet)
        assert max(all_output_octets) == pe.get_total_output_octets(stop_packet)

    def test_at_least_three_class_echoed(self, large_upload_pcap):
        """At least 3 Class attributes are echoed."""
        accept_packets = pe.get_accept_packets(large_upload_pcap)
        assert len(accept_packets) == 1
        classes_accept_packet = pe.get_values_for_attribute(accept_packets[0], 25)
        acct_req_packets = pe.get_packets_by_codes(large_upload_pcap, 4)
        # Go through each accounting packet and check if at least 3 classes are echoed
        for acct_packet in acct_req_packets:
            class_count = 0
            classes_acct_packet = pe.get_values_for_attribute(acct_packet, 25)
            for _class in classes_accept_packet:
                if _class in classes_acct_packet:
                    class_count += 1
            assert class_count >= 3

    def test_cui_echoed(self, large_upload_pcap):
        """Persistent CUI is echoed."""
        accept_packets = pe.get_accept_packets(large_upload_pcap)
        assert len(accept_packets) == 1
        cui_accept_packet = pe.get_values_for_attribute(accept_packets[0], 89)
        assert len(cui_accept_packet) == 1
        cui_to_look_for = cui_accept_packet[0]
        acct_req_packets = pe.get_packets_by_codes(large_upload_pcap, 4)
        # Go through each accounting packet and check if CUI is echoed
        for acct_packet in acct_req_packets:
            cui_acct_packet = pe.get_values_for_attribute(acct_packet, 89)
            assert cui_to_look_for in cui_acct_packet

    def __verify_usage_increasing(self, packets, octet_func: Callable):
        total_usage = 0
        stop_packets = pe.get_stop_packets(packets)
        update_packets = pe.get_update_packets(packets)
        rel_packets = update_packets + stop_packets
        # Verify total usage is increasing.
        for packet in rel_packets:
            prev_total_usage = total_usage
            total_usage = octet_func(packet)
            assert total_usage >= prev_total_usage

    def test_in_gigaword_rolls_over(self, large_download_pcap):
        """Acct-Input-Gigaword rolls over."""
        # Verify gigaword rollover by checking that the total usage is increasing.
        self.__verify_usage_increasing(large_download_pcap, pe.get_total_output_octets)

    def test_out_gigaword_rolls_over(self, large_upload_pcap):
        """Acct-Output-Gigaword rolls over."""
        # Verify gigaword rollover by checking that the total usage is increasing.
        self.__verify_usage_increasing(large_upload_pcap, pe.get_total_input_octets)


class TestAccuracyChecks:
    def get_octet_bounds(self, total_octets) -> Tuple[int, int]:
        """Get lower and upper bounds for octet count."""
        tolerance = 0.1
        return total_octets * (1 - tolerance), total_octets * (1 + tolerance)

    def __get_stop_or_update_packets(self, packets: List[Radius]) -> Radius:
        """Return Stop packet or latest Interim-Update+error."""
        try:
            packet = pe.get_stop_packets(packets)[0]
        except IndexError:
            logging.error("No Stop packet found, using latest Interim-Update.")
            packet = pe.get_update_packets(packets)[-1]
        return packet

    def __tonnage_accuracy(self, expected_octets, packets, octet_func: Callable):
        """General tonnage accuracy function."""
        expected_octets_low, expected_octets_high = self.get_octet_bounds(
            expected_octets
        )
        packet = self.__get_stop_or_update_packets(packets)
        total_octets = octet_func(packet)
        assert expected_octets_low <= total_octets <= expected_octets_high

    def test_input_tonnage_accuracy(self, large_upload_octets, large_upload_pcap):
        """Input tonnage is accurate."""
        self.__tonnage_accuracy(
            large_upload_octets, large_upload_pcap, pe.get_total_input_octets
        )

    def test_output_tonnage_accuracy(self, large_download_octets, large_download_pcap):
        """Output tonnage is accurate."""
        self.__tonnage_accuracy(
            large_download_octets, large_download_pcap, pe.get_total_output_octets
        )

    def test_session_duration_accuracy(
        self, large_download_duration, large_download_pcap
    ):
        """Session duration is accurate."""
        tolerance = 0.05
        packets = large_download_pcap
        session_time_lower_bound = large_download_duration * (1 - tolerance)
        session_time_upper_bound = large_download_duration * (1 + tolerance)
        packet = self.__get_stop_or_update_packets(packets)
        acct_session_times = pe.get_acct_session_time(packet)
        assert len(acct_session_times) == 1
        assert (
            session_time_lower_bound
            <= acct_session_times[0]
            <= session_time_upper_bound
        )

    def test_input_packet_count_nonzero(self, large_download_pcap):
        """Input Packet count is non-zero."""
        packets = large_download_pcap
        packet = self.__get_stop_or_update_packets(packets)
        input_packets_attributes = pe.get_acct_input_packets(packet)
        assert len(input_packets_attributes) == 1
        assert input_packets_attributes[0] > 0

    def test_output_packet_count_nonzero(self, large_download_pcap):
        """Output Packet count is non-zero."""
        packets = large_download_pcap
        packet = self.__get_stop_or_update_packets(packets)
        output_packets_attributes = pe.get_acct_output_packets(packet)
        assert len(output_packets_attributes) == 1
        assert output_packets_attributes[0] > 0


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


if __name__ == "__main__":
    test_name = "test1"
    pcap_dir = "/usr/local/raa/pcap"
    pcap, metadata = get_pcap_and_metadata(test_name, pcap_dir)

    # pytest.main()
