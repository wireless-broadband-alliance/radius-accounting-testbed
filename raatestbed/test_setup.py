import time
import os
import logging
import subprocess
import raatestbed.processes as procs
import yaml
import pytest
import json
from raatests.extra_funcs import get_metadata, Metadata
from datetime import datetime
from typing import List
from dataclasses import dataclass
from raatestbed.data_transfer import TCPServer, get_data_chunk


DEFAULT_ROOT_DIR = "/usr/local/raa"
DEFAULT_WIRELESS_IFACE = "wlan0"
DEFAULT_WIRED_IFACE = "eth0"
DEFAULT_CHUNK_SIZE = 1024**2
DEFAULT_SSID = "raatest"

@dataclass
class TestConfig:
    """Data class for storing test configuration"""
    test_name: str
    data_server_ip: str
    data_server_port: int
    chunk_size: int
    chunks: int
    data_server_listen_port: int
    ssid: str
    generate_pcap: bool
    generate_report: bool
    markers: List[str]
    client_interface: str
    server_interface: str
    local_output_directory: str

    @property
    def pcap_dir(self):
        return os.path.join(self.local_output_directory, "pcap")

    @property
    def logs_dir(self):
        return os.path.join(self.local_output_directory, "logs")

    @property
    def reports_dir(self):
        return os.path.join(self.local_output_directory, "reports")

    @property
    def configs_dir(self):
        return os.path.join(self.local_output_directory, "config")

    def __to_dict__(self):
        return self.__dict__

    def write_yaml(self):
        """Write test configuration to a YAML file"""
        config_filename = f"{self.test_name}.config.yaml"
        config = os.path.join(self.configs_dir, config_filename)
        logging.info(f"Writing test configuration to {config}")
        with open(config, 'w') as file:
            yaml.dump(self.__to_dict__(), file)


def setup_logging(debug):
    if debug:
        logging.basicConfig(
            level=logging.DEBUG, format="%(asctime)s - %(levelname)s: %(message)s"
        )
    else:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")



def create_dir_if_not_exists(directory):
    """Check if network interface has IP"""
    if not os.path.exists(directory):
        logging.info(f"Creating directory {directory}")
        os.makedirs(directory)


class TestSetup:
    """Class that contains common methods and attributes for all tests."""

    def __init__(self, 
                 test_config: TestConfig, 
                 logger: logging.Logger, 
                 debug=False):
        self.config = test_config
        self.debug = debug
        self.logger = logger
        self.logs_dir = self.config.logs_dir
        self.pcap_dir = self.config.pcap_dir
        self.__create_dirs()
        self.__initialize_proc_vars()

    def __create_dirs(self):
        """Create subdirectories for logs, pcap, configs, and reports"""
        for dir in [self.logs_dir, 
                    self.pcap_dir, 
                    self.config.configs_dir, 
                    self.config.reports_dir]:
            create_dir_if_not_exists(dir)

    def __initialize_proc_vars(self):
        """Initialize all processes variables"""
        self.freeradius = None
        self.wpasupplicant = None
        self.data_server = None
        self.radius_tcpdump = None

    def __check_for_ip(self):
        """Check if network interface has IP"""
        result = subprocess.run(
            ["ip", "addr", "show", self.config.client_interface],
            capture_output=True,
            text=True,
            check=True,
        )
        if "inet " in result.stdout:
            return True
        else:
            return False

    def __initialize_output_locations(self):
        """Initialize output locations for logs and pcap files"""
        test_name = self.config.test_name
        self.radius_tcpdump_log = os.path.join(
            self.logs_dir, f"{test_name}.tcpdump.radius.log"
        )
        self.freeradius_log = os.path.join(self.logs_dir, f"{test_name}.freeradius.log")
        self.radius_pcap_location = os.path.join(
            self.pcap_dir, f"{test_name}.tcpdump.radius.pcap"
        )
        self.wpa_supplicant_log = os.path.join(
            self.logs_dir, f"{test_name}.wpa_supplicant.log"
        )

    def __initialize_proc_objs(self):
        """Initialize process objects for the test"""
        self.__initialize_output_locations()
        self.radius_tcpdump = procs.TCPDump(
            interface=self.config.server_interface,
            pcap_location=self.radius_pcap_location,
            log_location=self.radius_tcpdump_log,
        )
        self.wpasupplicant = procs.WpaSupplicant(
            interface=self.config.client_interface,
            log_location=self.wpa_supplicant_log,
            ssid=self.config.ssid,
        )
        self.freeradius = procs.FreeRADIUS(
            log_location=self.freeradius_log, debug=self.debug
        )
        self.data_server = TCPServer(self.config.data_server_listen_port, self.config.chunk_size)

        self.username = self.wpasupplicant.get_username()

    def start(self, wait_for_ip=True, extra_wait_time=3):
        """Start processes"""
        self.stop()
        self.__initialize_proc_objs()
        self.logger.info(f'Starting test "{self.config.test_name}"...')

        def start_proc(proc):
            assert proc is not None
            proc.start()

        start_proc(self.radius_tcpdump)
        start_proc(self.freeradius)
        start_proc(self.data_server)
        start_proc(self.wpasupplicant)

        if wait_for_ip:
            # Block until wireless interface has IP
            self.logger.info(f"Waiting for IP on {self.config.client_interface}...")
            while not self.__check_for_ip():
                time.sleep(0.05)
        start_time = time.perf_counter()  # start counter after IP given
        time.sleep(extra_wait_time)  # wait for network to settle
        return start_time

    def stop(self):
        """Stop all processes"""

        def stop_proc(proc):
            if proc is not None:
                proc.stop()

        # Stop wpa_supplicant first to get Stop record in PCAP
        stop_proc(self.wpasupplicant)
        time.sleep(2)
        stop_proc(self.data_server)
        stop_proc(self.freeradius)
        time.sleep(1)
        stop_proc(self.radius_tcpdump)


def get_chunks(test_config: TestConfig, logger: logging.Logger, debug=False):
    test = TestSetup(test_config, debug=debug, logger=logger)
    chunks = test_config.chunks
    test.start()
    time.sleep(2)
    logging.info(f"pulling {chunks} chunks")
    begin = time.perf_counter()
    for num in range(chunks):
        logging.info(f"pulling chunk {num+1} of {chunks}")
        get_data_chunk(
            server_host=test_config.data_server_ip,
            server_port=test_config.data_server_port,
            chunk_size=test_config.chunk_size,
            iface=test_config.client_interface
        )
    end = time.perf_counter()
    logging.info(f"Download completed in {end - begin:.2f} seconds")
    test.stop()

def select_markers():
    """Select markers from a list."""

    # TODO: These should be generated dynamically
    options_mapping = {
        "1": "core",
        "2": "core_download",
        "3": "core_upload",
        "4": "openroaming",
    }
    print("\nSelect tests suite(s) from the list:")
    for key, value in options_mapping.items():
        print(f"{key}) {value}")
    print("")

    selected_options = []
    user_input = input("Enter your options (comma-separated numbers): ")
    selected_options = [
        options_mapping.get(choice.strip(), "") for choice in user_input.split(",")
    ]
    selected_options = [option for option in selected_options if option]

    return ", ".join(selected_options), " or ".join(selected_options)

def execute_test_cases(config: TestConfig):
    """Run tests against PCAP."""
    test_name = config.test_name
    metadata = get_metadata(test_name, config.pcap_dir)
    logging.info(f'\n\nMetadata for "{test_name}":\n{metadata.pretty_print_format()}\n')
    markers_txt, markers = select_markers()
    pytest_args = ["-v", "raatests", "--test_name", test_name]
    extra_args = ["-m", markers]
    if user_wants_to_continue(f'Running test suites "{markers_txt}"'):
        pytest.main(pytest_args + extra_args)

def user_wants_to_continue(prompt_message):
    user_input = input(f"{prompt_message} (yes/no): ").strip().lower()

    if user_input == "yes":
        return True
    elif user_input == "no":
        return False
    else:
        print("Invalid input. Please enter 'yes' or 'no'.")
        return user_wants_to_continue(prompt_message)



def generate_pcap(test_config: TestConfig, 
                  logger: logging.Logger, 
                  debug=False):
    """Run end-to-end test and generate PCAP + PCAP metadata."""

    test = TestSetup(test_config, debug=debug, logger=logger)
    chunks = test_config.chunks

    # Start test for PCAP generation.
    begin = test.start()
    time.sleep(2)

    # Start data transfer.
    logger.info(f"pulling {chunks} chunks")
    start_time = datetime.now()
    begin_data_transfer = time.perf_counter()
    for num in range(chunks):
        logger.info(f"pulling chunk {num+1} of {chunks}")
        get_data_chunk(
            server_host=test_config.data_server_ip,
            server_port=test_config.data_server_port,
            chunk_size=test_config.chunk_size,
            iface=test_config.client_interface
        )

    # Data transfer completed, stop test.
    end = time.perf_counter()
    end_time = datetime.now()
    session_duration = int(end - begin)
    data_transfer_duration = end - begin_data_transfer
    logger.info(f"Download completed in {data_transfer_duration:.2f} seconds")
    test.stop()

    # Write test metadata to file.
    filename = f"{test_config.test_name}.metadata.json"
    filename_withdir = os.path.join(test.pcap_dir, filename)
    test_metadata = Metadata(
        username=test.username,
        session_duration=session_duration,
        chunk_size=str(test_config.chunk_size),
        chunks=str(chunks),
        start_time=start_time,
        end_time=end_time,
    )
    test_metadata_dict = test_metadata.get_dict()

    logger.info(f'Writing metadata to file "{filename_withdir}"')
    with open(filename_withdir, "w") as f:
        json.dump(test_metadata_dict, f)

