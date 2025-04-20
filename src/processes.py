"""Contains process-related imports."""

from string import Template
from uuid import uuid4
import subprocess
import time
import signal
import os
import threading
import logging
from src.inputs import SSID as DEFAULT_SSID


class Command:
    """Base class for running commands in background and writing to log file"""

    def __init__(self, name: str, command: list, log_file, wait_time=None, env=None):
        self.command = command
        self.name = name
        self.log_file = log_file
        self.wait_time = wait_time
        self.process = None
        self.thread = None
        if env is not None:
            base_env = os.environ.copy()
            self.env = {**base_env, **env}
        else:
            self.env = None

        # Create directory for log file if it doesn't exist
        directory = os.path.dirname(log_file)
        if not os.path.exists(directory):
            logging.info(f"Creating directory {directory}")
            os.makedirs(directory)

    def run_subprocess(self):
        # write to log file, append if needed
        with open(self.log_file, "a") as log:
            if self.env:
                self.process = subprocess.Popen(self.command, stdout=log, stderr=log, env=self.env)
            else:
                self.process = subprocess.Popen(self.command, stdout=log, stderr=log)
            self.process.wait()

    def start(self):
        """Run command in background, return process object"""
        logging.info(f"Starting {self.name}...")
        self.thread = threading.Thread(target=self.run_subprocess)
        self.thread.start()

        # We will know if there was a problem if the process ends after <wait_time> seconds
        if self.wait_time is not None:
            time.sleep(self.wait_time)
            assert self.process is not None
            if not self.thread.is_alive():
                return_code = self.process.returncode
                raise Exception(
                    f"Command ended with within {self.wait_time} seconds with return code: {return_code}"
                )

    def stop(self):
        if self.process is not None:
            logging.info(f"Stopping {self.name}...")
            pid = self.process.pid
            os.kill(pid, signal.SIGTERM)
            # self.process.kill()
            self.process = None
            self.thread = None
        else:
            logging.debug(f"process {self.name} already stopped...")


class WpaSupplicant(Command):
    """Control WPA supplicant instance"""

    def __init__(
        self,
        interface,
        log_location,
        ssid=DEFAULT_SSID,
        wait_time=5,
        config_location="/tmp/wpa_supplicant.conf",
    ):
        self.interface = interface
        self.log_location = log_location
        self.ssid = ssid
        self.config_location = config_location
        self.wait_time = wait_time
        self.username = None
        self.initialize()

    def initialize(self):
        """Write new wpa_supplicant config file and get command"""
        self.write_wpa_supplicant_conf()
        cmd = [
            "wpa_supplicant",
            "-c",
            self.config_location,
            "-i",
            self.interface,
        ]
        super().__init__("wpa_supplicant", cmd, self.log_location, self.wait_time)

    def get_username(self) -> str:
        if self.username is None:
            return ""
        return self.username

    def __get_wpa_supplicant_conf(
        self, identity="raauser@example.com", password="secret"
    ):
        """Return random username and WPA supplicant config file"""

        # Get random username
        uuid = uuid4()
        anonymous_identity = f"{uuid}@example.com"

        ssid = self.ssid

        # Create example config file template
        template = Template(
            """
                network={
                    ssid="$ssid"
                    proto=RSN
                    key_mgmt=WPA-EAP
                    eap=TTLS
                    identity="$identity"
                    anonymous_identity="$anonymous_identity"
                    password="$password"
                    phase2="eapauth=MSCHAPV2"
                }
            """
        )

        # Return anonymous_identity and template with spaces removed
        return anonymous_identity, template.substitute(
            anonymous_identity=anonymous_identity,
            identity=identity,
            password=password,
            ssid=ssid,
        ).replace(" ", "")

    def write_wpa_supplicant_conf(self):
        """Write WPA supplicant config file to disk"""
        # Get string contents of config file
        username, config_contents = self.__get_wpa_supplicant_conf()

        logging.debug(f"Writing WPA supplicant config to {self.config_location}")

        # Write config to disk
        with open(self.config_location, "w") as file:
            file.write(config_contents)
        self.username = username


class FreeRADIUS(Command):
    """Control FreeRADIUS instance"""

    def __init__(
        self,
        log_location,
        wait_time=5,
        debug=False,
        port=1812,
    ):
        env = {}
        env['AUTH_PORT'] = str(port)
        env['ACCT_PORT'] = str(int(port) + 1)
        self.log_location = log_location
        self.wait_time = wait_time
        if debug:
            cmd = ["freeradius", "-f", "-l", "stdout", "-xx"]
        else:
            cmd = ["freeradius", "-f", "-l", "stdout"]
        subprocess.Popen(["systemctl", "stop", "freeradius.service"])

        super().__init__("FreeRADIUS", cmd, self.log_location, self.wait_time, env=env)


class TCPDump(Command):
    """Control tcpdump instance"""

    def __init__(
        self,
        pcap_location,
        log_location,
        interface="eth0",
        wait_time=2,
        filter="port 1812 or port 1813",
    ):
        log_location = log_location
        wait_time = wait_time
        cmd = ["tcpdump", "-i", interface, "-w", pcap_location, filter]
        super().__init__("tcpdump", cmd, log_location, wait_time)
