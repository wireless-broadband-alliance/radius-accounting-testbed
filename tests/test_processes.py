import sys
import os
import time
import subprocess
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.processes import Command, FreeRADIUS, WpaSupplicant

EXPECTED_TEXT = "this_is_a_test"

class TestCommand(Command):
    """Control Test Command"""
    def __init__(
        self,
        log_location,
        wait_time=1,
    ):
        # create cmd to print test string over and over
        cmd = ["sh", "-c", f"while true; do echo {EXPECTED_TEXT}; sleep 1; done"]
        super().__init__("TestCommand", cmd, log_location, wait_time)

def remove_file(file):
    try:
        os.remove(file)
    except FileNotFoundError:
        pass

def test_simple_command():
    """Test a simple command"""
    log_location = '/tmp/test.log'
    remove_file(log_location)
    cmd = TestCommand(log_location)
    cmd.start()
    time.sleep(10)
    cmd.stop()
    
    assert os.path.exists(log_location)

    # Assert that the log file contains the expected text, remove file before asserting
    with open(log_location, 'r') as f:
        assert EXPECTED_TEXT in f.read()

def test_freeradius():
    """Test freeradius"""

    log_location = '/tmp/freeradius.log'
    remove_file(log_location)
    radius = FreeRADIUS(log_location=log_location, debug=True)
    radius.start()
    time.sleep(10)
    radius.stop()
    assert os.path.exists(log_location)
    with open(log_location, 'r') as f:
        assert "Ready to process requests" in f.read()

def test_wpasupplicant():
    """Test WPA supplicant"""

    log_location = '/tmp/wpasupplicant.log'
    config_location = '/tmp/wpa_supplicant.conf'
    interface = "wlan0"
    remove_file(log_location)
    remove_file(config_location)
    supplicant = WpaSupplicant(interface=interface, 
                               log_location=log_location, 
                               config_location=config_location,
                               cmd=["wpa_supplicant", "-c", config_location, "-i", "lo", "-D", "wired"])
    supplicant.start()
    time.sleep(10)
    supplicant.stop()
    assert os.path.exists(log_location)
    with open(log_location, 'r') as f:
        assert "Successfully initialized wpa_supplicant" in f.read()