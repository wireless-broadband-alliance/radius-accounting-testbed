"""OpenRoaming tests (Proof of Concept)."""

from typing import List
import re
import pytest
from scapy.all import Radius
import src.pcap_extract as pe


class TestOpenroamAttributes:
    """Test OpenRoaming-related RADIUS attributes in RADIUS packets."""

    @pytest.mark.openroaming
    def test_operator_name_format(self, packets: List[Radius]):
        """Go through each packet and check if Operator-Name is present"""

        # https://datatracker.ietf.org/doc/draft-tomas-openroaming/ section 8.1
        not_present_counter = 0
        for packet in packets:
            operator_names = pe.get_values_for_attribute(packet, 126)
            try:
                # Check only one Operator-Name is present.
                assert len(operator_names) == 1
            except AssertionError:
                not_present_counter += 1
            else:
                # Check operator-name is in correct format.
                assert re.match(r"4.+:[A-Z]{2}", operator_names[0])
        if not_present_counter:
            print(
                f"Operator-Name not in {not_present_counter} of {len(packets)} packets."
            )
            raise ValueError("Operator-Name not present in all packets.")
