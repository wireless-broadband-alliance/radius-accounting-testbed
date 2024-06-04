from scapy.all import rdpcap, Radius
from typing import List, Union

# from IPython import embed


def get_radius_packets(pcap_file: str) -> List[Radius]:
    """Find RADIUS packets in a PCAP file and return just the RADIUS layers."""
    radius_packets = []
    # Iterate through the packets to find RADIUS packets with the specified username
    packets = rdpcap(pcap_file)
    # embed()
    for packet in packets:
        # Look for RADIUS packets.
        if packet.haslayer(Radius):
            radius_packets.append(packet[Radius])
    return radius_packets


def __filter_packets(
    packets: List[Radius], _type: int, value, vendor: Union[int, None] = None
) -> List[Radius]:
    """Filter RADIUS packets based on a specific attribute type and value."""
    filtered_packets = []
    if vendor == 0:
        vendor = None
    for packet in packets:
        for attribute in packet.attributes:
            fields = attribute.fields
            if (
                (fields.get("vendor") == vendor)
                & (fields.get("type") == _type)
                & (fields.get("value") == value)
            ):
                filtered_packets.append(packet[Radius])
                break

    return filtered_packets


def get_packets_by_username(packets: List[Radius], username: str) -> List[Radius]:
    """Look for RADIUS packets with a specific username"""
    username_bytes = bytes(username, "utf-8")
    return __filter_packets(packets, 1, username_bytes)


def get_relevant_packets(pcap: str, username: str) -> List[Radius]:
    """Read PCAP and just return packets we are interested in."""
    all_radius_packets = get_radius_packets(pcap)
    return get_packets_by_username(packets=all_radius_packets, username=username)


def get_latest_radius_packet(packets: List[Radius]) -> Radius:
    """Get the RADIUS packet with the latest timestamp"""
    latest_timestamp = 0
    latest_radius_packet = None
    for packet in packets:
        packet_timestamp = packet.time
        if packet_timestamp > latest_timestamp:
            latest_timestamp = packet_timestamp
            latest_radius_packet = packet
    return latest_radius_packet


def get_values_for_attribute(
    packet: Radius, _type: int, vendor: Union[int, None] = None
) -> list:
    """Get values for a specific attribute in a RADIUS packet"""
    if vendor == 0:
        vendor = None
    field_values = []
    for attribute in packet.attributes:
        fields = attribute.fields
        if (fields.get("type") == _type) & (fields.get("vendor_id") is None):
            field_values.append(attribute.value)
        elif (
            (fields.get("type") == 26)
            & (fields.get("vendor_id") == vendor)
            & (fields.get("vendor_type") == _type)
        ):
            field_values.append(attribute.value)
    return field_values


def get_packets_by_codes(packets: List[Radius], *codes) -> List[Radius]:
    """Look for RADIUS packets with a specific code"""
    packets_out = []
    for packet in packets:
        if packet.code in codes:
            packets_out.append(packet)
    return packets_out


def get_accept_packets(packets: List[Radius]) -> List[Radius]:
    """Look for Access-Accept packets"""
    return get_packets_by_codes(packets, 2)


def get_start_packets(packets: List[Radius]) -> List[Radius]:
    """Look for packets with Acct-Status-Type as Start"""
    return __filter_packets(packets, 40, 1)


def get_update_packets(packets: List[Radius]) -> List[Radius]:
    """Look for packets with Acct-Status-Type as Update"""
    return __filter_packets(packets, 40, 3)


def get_stop_packets(packets: List[Radius]) -> List[Radius]:
    """Look for packets with Acct-Status-Type as Stop"""
    return __filter_packets(packets, 40, 2)


def get_acct_session_id(packet: Radius) -> list:
    """Get all values of Acct-Session-Id from a RADIUS packet"""
    return get_values_for_attribute(packet, 44)


def get_acct_input_octets(packet: Radius) -> list:
    """Get all values of Acct-Input-Octets from a RADIUS packet"""
    return get_values_for_attribute(packet, 42)


def get_acct_input_gigawords(packet: Radius) -> list:
    """Get all values of Acct-Input-Gigawords from a RADIUS packet"""
    return get_values_for_attribute(packet, 52)


def get_acct_output_octets(packet: Radius) -> list:
    """Get all values of Acct-Output-Octets from a RADIUS packet"""
    return get_values_for_attribute(packet, 43)


def get_acct_output_gigawords(packet: Radius) -> list:
    """Get all values of Acct-Output-Gigawords from a RADIUS packet"""
    return get_values_for_attribute(packet, 53)


def __check_for_one_value(attribute_list: list, attribute_name: str):
    """Check that there is only one in attribute list."""
    if len(attribute_list) != 1:
        # TODO: Different exception types?
        raise Exception(f"Attribute {attribute_name} should have one value")


def get_total_output_octets(packet: Radius) -> int:
    """Get total output usage for a RADIUS packet"""
    gigawords = get_acct_output_gigawords(packet)
    octets = get_acct_output_octets(packet)
    # Verify that there is only one value for each attribute
    __check_for_one_value(gigawords, "Acct-Output-Gigawords")
    __check_for_one_value(octets, "Acct-Output-Octets")
    return calculate_total_octets(octets[0], gigawords[0])


def get_total_input_octets(packet: Radius) -> int:
    """Get total input usage for a RADIUS packet"""
    gigawords = get_acct_input_gigawords(packet)
    octets = get_acct_input_octets(packet)
    # Verify that there is only one value for each attribute
    __check_for_one_value(gigawords, "Acct-Input-Gigawords")
    __check_for_one_value(octets, "Acct-Input-Octets")
    return calculate_total_octets(octets[0], gigawords[0])


def get_acct_input_packets(packet: Radius) -> list:
    """Get all values of Acct-Input-Packets from a RADIUS packet"""
    return get_values_for_attribute(packet, 47)


def get_acct_output_packets(packet: Radius) -> list:
    """Get all values of Acct-Output-Packets from a RADIUS packet"""
    return get_values_for_attribute(packet, 48)


def get_acct_session_time(packet: Radius) -> list:
    """Get all values of Acct-Session-Time from a RADIUS packet"""
    return get_values_for_attribute(packet, 46)


def calculate_total_octets(octets: int, gigawords: int) -> int:
    """Calculate total Acct-*-Octets and Acct-*-Gigawords."""
    return octets + (gigawords * 2**32)


if __name__ == "__main__":
    username = "1542aeee-0c55-404c-badf-ccc5093d10ca@example.com"
    input_pcap = "pcaps/test_dl_5gb.tcpdump.radius.pcap"
    packets = get_relevant_packets(input_pcap, username)
    # embed()
