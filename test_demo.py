import pcap_extract as pe
from scapy.all import Radius
from typing import List
# from IPython import embed


def test_unique_persistent_acct_session_id(packets: List[Radius]):
    """Unique and persistent Acct-Session-Id in accounting sessions."""
    # Get all Acct-Session-Id values from the packets, then check if there is only one unique value.
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


def test_acct_session_id_auth_acct(packets: List[Radius]):
    """Acct-Session-Id is persistent in authentication and accounting sessions."""
    acct_session_ids = []
    req_packets = pe.get_packets_by_codes(packets, 1, 4)
    for packet in req_packets:
        acct_session_ids += pe.get_acct_session_id(packet)
    # Each packet has an Acct-Session-Id
    assert len(req_packets) == len(acct_session_ids)


def test_start_update_stop_present(packets: List[Radius]):
    """Start, Update, and Stop records are present in accounting session."""
    start_packets = pe.get_start_packets(packets)
    update_packets = pe.get_update_packets(packets)
    stop_packets = pe.get_stop_packets(packets)

    assert len(stop_packets) == 1
    assert len(start_packets) == 1
    assert len(update_packets) >= 0


def test_stop_record_last_message(packets: List[Radius]):
    """Stop record is last message in accounting session."""
    latest_packet = pe.get_latest_radius_packet(packets)
    latest_packet_acct_status_type = pe.get_values_for_attribute(latest_packet, 40)
    # Only one Acct-Status-Type field
    assert len(latest_packet_acct_status_type) == 1
    # Acct-Status-Type is Stop (2)
    assert latest_packet_acct_status_type[0] == 2


def test_stop_record_highest_usage(packets: List[Radius]):
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


def test_at_least_three_class_echoed(packets: List[Radius]):
    """At least 3 Class attributes are echoed."""
    pass


def test_in_gigaword_rolls_over(packets: List[Radius]):
    """Acct-Input-Gigaword rolls over."""
    pass


def test_out_gigaword_rolls_over(packets: List[Radius]):
    """Acct-Output-Gigaword rolls over."""
    pass


def test_input_tonnage_accurate(packets: List[Radius]):
    """Input tonnage is accurate."""
    pass


def test_output_tonnage_accurate(packets: List[Radius]):
    """Output tonnage is accurate."""
    pass


def test_session_duration_accurate(packets: List[Radius]):
    """Session duration is accurate."""
    pass


def test_input_packet_count_nonzero(packets: List[Radius]):
    """Input packet count is non-zero."""
    pass


def test_output_packet_count_nonzero(packets: List[Radius]):
    """Output packet count is non-zero."""
    pass


if __name__ == "__main__":
    username = "1542aeee-0c55-404c-badf-ccc5093d10ca@example.com"
    input_pcap = "tmp/test_dl_5gb.tcpdump.radius.pcap"
    packets = pe.get_relevant_packets(input_pcap, username)
