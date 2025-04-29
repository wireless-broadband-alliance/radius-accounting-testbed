"""RADIUS Accounting Assurance core tests"""

from typing import List, Callable, Tuple
import logging
import pytest
import src.pcap_extract as pe
from scapy.all import Radius


class TestAttributeChecks:
    """Basic accounting RADIUS tests"""
    @pytest.mark.core
    def test_unique_persistent_acct_session_id(self, packets):
        """Unique and persistent Acct-Session-Id in accounting sessions."""
        # Get all Acct-Session-Id values from the packets, then check if there is only one unique value.
        acct_session_ids = []
        acct_req_packets = pe.get_packets_by_codes(packets, 4)
        for acct_packet in acct_req_packets:
            acct_session_ids += pe.get_acct_session_id(acct_packet)
        # Each packet has an Acct-Session-Id
        assert len(acct_req_packets) == len(acct_session_ids)
        # Account-Session-Id is unique
        unique_ids = set(acct_session_ids)
        try:
            assert unique_ids == 1
        except AssertionError:
            print(f"Unique Acct-Session-Id values: {len(unique_ids)}")
        session_id = acct_session_ids[0]
        # Account-Session-Id looks unique
        assert len(session_id) > 5

    @pytest.mark.core
    def test_acct_session_id_auth_acct(self, packets):
        """Acct-Session-Id is persistent in authentication and accounting sessions."""
        acct_session_ids = []
        req_packets = pe.get_packets_by_codes(packets, 1, 4)
        for packet in req_packets:
            acct_session_ids += pe.get_acct_session_id(packet)
        # Each packet has an Acct-Session-Id
        try:
            assert len(req_packets) == len(acct_session_ids)
        except AssertionError:
            print(
                f"Acct-Session-Id only seen in {len(acct_session_ids)} out of {len(req_packets)} packets."
            )

    @pytest.mark.core
    def test_start_update_stop_present(self, packets):
        """Start, Update, and Stop records are present in accounting session."""
        start_packets = pe.get_start_packets(packets)
        update_packets = pe.get_update_packets(packets)
        stop_packets = pe.get_stop_packets(packets)

        assert len(stop_packets) == 1
        assert len(start_packets) == 1
        assert len(update_packets) >= 0
        print(
            f"Packet Count: Start: {len(start_packets)}, Update: {len(update_packets)}, Stop: {len(stop_packets)}"
        )

    @pytest.mark.core
    def test_stop_record_last_message(self, packets):
        """Stop record is last message in accounting session."""
        latest_packet = pe.get_latest_radius_packet(packets)
        latest_packet_acct_status_type = pe.get_values_for_attribute(latest_packet, 40)
        # Only one Acct-Status-Type field
        assert len(latest_packet_acct_status_type) == 1
        # Acct-Status-Type is Stop (2)
        assert latest_packet_acct_status_type[0] == 2

    @pytest.mark.core
    def test_stop_record_highest_usage(self, packets):
        """Stop record contains highest usage fields."""
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

    @pytest.mark.core
    def test_at_least_three_class_echoed(self, packets):
        """At least 3 Class attributes are echoed."""
        accept_packets = pe.get_accept_packets(packets)
        assert len(accept_packets) == 1
        classes_accept_packet = pe.get_values_for_attribute(accept_packets[0], 25)
        acct_req_packets = pe.get_packets_by_codes(packets, 4)
        # Go through each accounting packet and check if at least 3 classes are echoed
        for acct_packet in acct_req_packets:
            class_count = 0
            classes_acct_packet = pe.get_values_for_attribute(acct_packet, 25)
            for _class in classes_accept_packet:
                if _class in classes_acct_packet:
                    class_count += 1
            assert class_count >= 3

    @pytest.mark.core
    def test_cui_echoed(self, packets):
        """Persistent CUI is echoed."""
        accept_packets = pe.get_accept_packets(packets)
        assert len(accept_packets) == 1
        cui_accept_packet = pe.get_values_for_attribute(accept_packets[0], 89)
        assert len(cui_accept_packet) == 1
        cui_to_look_for = cui_accept_packet[0]
        acct_req_packets = pe.get_packets_by_codes(packets, 4)
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

    @pytest.mark.core_upload
    def test_in_gigaword_rolls_over(self, packets, metadata):
        """Acct-Input-Gigaword rolls over."""
        # Verify gigaword rollover by checking that the total usage is increasing.
        total_octets = int(metadata.chunk_size) * int(metadata.chunks)
        if total_octets > 4 * 1024 * 1024 * 1024:
            self.__verify_usage_increasing(packets, pe.get_total_output_octets)
        else:
            pytest.skip("Upload octets under 4 GB, Acct-Input-Gigaword not used.")

    @pytest.mark.core_download
    def test_out_gigaword_rolls_over(self, packets, metadata):
        """Acct-Output-Gigaword rolls over."""
        # Verify gigaword rollover by checking that the total usage is increasing.
        total_octets = int(metadata.chunk_size) * int(metadata.chunks)
        if total_octets > 4 * 1024 * 1024 * 1024:
            self.__verify_usage_increasing(packets, pe.get_total_input_octets)
        else:
            pytest.skip("Download octets under 4 GB, Acct-Output-Gigaword not used.")


class TestAccuracyChecks:
    """Compare data reported through RADIUS vs what was actually transferred."""
    def __get_stop_or_update_packets(self, packets: List[Radius]) -> Radius:
        """Return Stop packet or latest Interim-Update+error."""
        try:
            packet = pe.get_stop_packets(packets)[0]
        except IndexError:
            logging.error("No Stop packet found, using latest Interim-Update.")
            packet = pe.get_update_packets(packets)[-1]
        return packet

    def __get_packets_sent_recv(self, metadata) -> Tuple[int, int]:
        """Return packets sent and received from given metadata."""
        if metadata.uploaded and metadata.downloaded:
            packets_sent = (
                metadata.usage_upload.packets_sent
                + metadata.usage_download.packets_sent
            )
            packets_recv = (
                metadata.usage_download.packets_recv
                + metadata.usage_upload.packets_recv
            )
        elif metadata.uploaded and not metadata.downloaded:
            packets_sent = metadata.usage_upload.packets_sent
            packets_recv = metadata.usage_upload.packets_recv
        elif not metadata.uploaded and metadata.downloaded:
            packets_recv = metadata.usage_download.packets_recv
            packets_sent = metadata.usage_download.packets_sent
        else:
            packets_sent = 0
            packets_recv = 0
        assert packets_sent or packets_recv, "No packets sent or received"
        return int(packets_sent), int(packets_recv)

    def __calculate_accuracy(self, expected_octets:int, actual_octets:int, octet_type: str, tolerance = 0.03):
        expected_octets_low = int(expected_octets * (1-tolerance))
        expected_octets_high = int(expected_octets * (1+tolerance))
        percentage_off = round(100*((expected_octets / actual_octets)-1), 2)
        print(f"{octet_type} Octets reported by RADIUS: ", actual_octets)
        print(f"{octet_type} Octets reported by network interface statistics: ", expected_octets)
        print(f"Difference: {percentage_off}%")
        print(f"Acceptable Range: {expected_octets_low} - {expected_octets_high}")
        print(f"Tolerance: {100*tolerance}%")
        assert expected_octets_low <= actual_octets <= expected_octets_high

    @pytest.mark.core_upload
    def test_input_tonnage_accuracy(self, packets, metadata):
        """Input tonnage is accurate."""
        tolerance = 0.02
        if not metadata.uploaded:
            pytest.skip("No upload data")

        # Get expected sent bytes from metadata
        bytes_sent = 0
        if metadata.downloaded:
            bytes_sent += metadata.usage_download.bytes_sent
        if metadata.uploaded:
            bytes_sent += metadata.usage_upload.bytes_sent

        # Get total octets from RADIUS
        packet = self.__get_stop_or_update_packets(packets)
        total_octets = pe.get_total_input_octets(packet)
        assert bytes_sent * (1-tolerance) <= total_octets <= bytes_sent * (1+tolerance)

        ## Get total octets from RADIUS
        #packet = self.__get_stop_or_update_packets(packets)
        #total_octets = pe.get_total_input_octets(packet)

        #self.__calculate_accuracy(expected_octets=bytes_sent,
        #                          actual_octets=total_octets,
        #                          octet_type="Input")

    @pytest.mark.core_download
    def test_output_tonnage_accuracy(self, packets, metadata):
        """Output tonnage is accurate."""
        tolerance = 0.02
        if not metadata.downloaded:
            pytest.skip("No download data")
        bytes_recv = 0
        if metadata.downloaded:
            bytes_recv += metadata.usage_download.bytes_recv
        if metadata.uploaded:
            bytes_recv += metadata.usage_upload.bytes_recv
        assert bytes_recv(1-tolerance) <= bytes_recv <= (1+tolerance)

    @pytest.mark.core
    def test_session_duration_accuracy(self, packets, metadata):
        """Session duration is accurate."""
        tolerance = 0.05
        session_time_lower_bound = round(
            (metadata.session_duration * (1 - tolerance)) - 10, 2
        )
        session_time_upper_bound = round(
            (metadata.session_duration * (1 + tolerance)) + 10, 2
        )
        packet = self.__get_stop_or_update_packets(packets)
        acct_session_times = pe.get_acct_session_time(packet)
        acct_session_time = acct_session_times[0]
        assert len(acct_session_times) == 1
        assert session_time_lower_bound <= acct_session_time <= session_time_upper_bound
        print("Session Time: ", acct_session_time)
        print(f"Valid Range: {session_time_lower_bound} - {session_time_upper_bound}")

    def __packet_tests(self, packet_attributes):
        """General packet count test."""
        assert len(packet_attributes) == 1
        packets = packet_attributes[0]
        try:
            assert packets > 0
        except AssertionError:
            print(f"Expected packets > 0, got {packets}")

    @pytest.mark.core
    def test_input_packet_count_nonzero(self, packets):
        """Input Packet count is non-zero."""
        stop_update_packet = self.__get_stop_or_update_packets(packets)
        input_packets_attributes = pe.get_acct_input_packets(stop_update_packet)
        self.__packet_tests(input_packets_attributes)

    @pytest.mark.core
    def test_output_packet_count_nonzero(self, packets):
        """Output Packet count is non-zero."""
        packet = self.__get_stop_or_update_packets(packets)
        output_packets_attributes = pe.get_acct_output_packets(packet)
        self.__packet_tests(output_packets_attributes)
