import pcap_extract as pe
from scapy.all import Radius
from typing import List, Callable, Tuple
import logging
import pytest
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
    username = "519c25f2-7c0e-4e86-8d7f-023802443f63@example.com"
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

    @pytest.mark.skip(reason="not implemented yet")
    def test_at_least_three_class_echoed(self, large_download_pcap):
        """At least 3 Class attributes are echoed."""
        pass

    @pytest.mark.skip(reason="not implemented yet")
    def test_cui_echoed(self, large_download_pcap):
        """At least 3 CUIs are echoed."""
        pass

    def __gigaword_rolls_over(self, packets, octet_func: Callable):
        total_usage = 0
        stop_packets = pe.get_stop_packets(packets)
        update_packets = pe.get_update_packets(packets)
        rel_packets = update_packets + stop_packets
        for packet in rel_packets:
            prev_total_usage = total_usage
            total_usage = octet_func(packet)
            assert total_usage >= prev_total_usage

    def test_in_gigaword_rolls_over(self, large_download_pcap):
        """Acct-Input-Gigaword rolls over."""
        self.__gigaword_rolls_over(large_download_pcap, pe.get_total_output_octets)

    def test_out_gigaword_rolls_over(self, large_upload_pcap):
        """Acct-Output-Gigaword rolls over."""
        self.__gigaword_rolls_over(large_upload_pcap, pe.get_total_input_octets)


class TestAccuracyChecks:
    def get_octet_bounds(self, total_octets) -> Tuple[int, int]:
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

    def test_packet_count_nonzero(self, large_download_pcap):
        """Packet count is non-zero."""
        packets = large_download_pcap
        packet = self.__get_stop_or_update_packets(packets)
        output_packets_attributes = pe.get_acct_output_packets(packet)
        input_packets_attributes = pe.get_acct_input_packets(packet)
        assert len(output_packets_attributes) == 1
        assert len(input_packets_attributes) == 1
        assert output_packets_attributes[0] > 0
        assert input_packets_attributes[0] > 0
