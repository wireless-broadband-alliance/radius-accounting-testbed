import raatestbed.pcap_extract as pe
from scapy.all import Radius
from typing import List
import re
import pytest


class TestOpenroamAttributes:
    @pytest.mark.openroaming
    def test_operator_name_format(self, packets: List[Radius]):
        """Go through each packet and check if Operator-Name is present"""
        # https://datatracker.ietf.org/doc/draft-tomas-openroaming/ section 8.1
        for packet in packets:
            operator_names = pe.get_values_for_attribute(packet, 126)
            # Check only one Operator-Name is present.
            assert len(operator_names) == 1
            # Check operator-name is in correct format.
            assert re.match(r"4.+:[A-Z]{2}", operator_names[0])
