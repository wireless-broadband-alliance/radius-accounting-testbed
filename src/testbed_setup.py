"""Contains test setup-related imports."""

from datetime import datetime
from typing import List
from dataclasses import dataclass
import time
import os
import sys
import logging
import subprocess
import json
import yaml

import src.processes as procs
import src.files as files
import src.inputs as inputs
from src.data_transfer import TCPServer
from src.metadata import Metadata


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
    upload_chunks: bool
    download_chunks: bool
    markers: List[str]
    client_interface: str
    server_interface: str
    local_output_directory: str
    sut_brand: str
    sut_hardware: str
    sut_software: str
    radius_port: int

    @property
    def pcap_dir(self):
        return files.get_pcap_dir(self.local_output_directory)

    @property
    def logs_dir(self):
        return files.get_logs_dir(self.local_output_directory)

    @property
    def reports_dir(self):
        return files.get_reports_dir(self.local_output_directory)

    @property
    def configs_dir(self):
        return files.get_config_dir(self.local_output_directory)

    def __to_dict__(self):
        return self.__dict__

    def pretty_print(self):
        for key, value in self.__to_dict__().items():
            if isinstance(value, list):
                value = ", ".join(value)
            print(f"{key}: {value}")

    def write_yaml(self):
        """Write test configuration to a YAML file"""
        config = files.get_config_filename(self.test_name, self.local_output_directory)
        logging.info("Writing test configuration to %s", config)
        with open(config, "w", encoding='utf-8') as file:
            yaml.dump(self.__to_dict__(), file)

def get_possible_markers():
    """Generate markers from pytest.ini file."""
    curdir = os.path.dirname(os.path.abspath(__file__))
    pytest_ini_file = os.path.join(curdir, inputs.RELATIVE_PYTEST_INI)
    return files.get_marker_list(pytest_ini_file)

def get_testconfig(test_name: str,
                   data_server_ip: str,
                   data_server_port: int,
                   cliargs: dict,
                   configargs: dict | None) -> TestConfig:
    """Create TestConfig object with CLI + config args. A TestConfig object is needed for executing tests."""

    #Merge CLI + config + default args. CLI args take precedence.
    all_opts = inputs.get_all_args(cliargs, configargs)

    #Create final TestConfig object using merged args from CLI + config + defaults.
    #TODO: Clean this up!
    test_config = TestConfig(
        test_name=test_name,
        data_server_ip=data_server_ip,
        data_server_port=data_server_port,
        data_server_listen_port=all_opts[inputs.KEY_DATA_SERVER_LISTEN_PORT],
        chunk_size=all_opts[inputs.KEY_CHUNK_SIZE],
        chunks=all_opts[inputs.KEY_CHUNKS],
        ssid=all_opts[inputs.KEY_SSID],
        generate_pcap=all_opts[inputs.KEY_GENERATE_PCAP],
        generate_report=all_opts[inputs.KEY_GENERATE_REPORT],
        upload_chunks=all_opts[inputs.KEY_UPLOAD_CHUNKS],
        download_chunks=all_opts[inputs.KEY_DOWNLOAD_CHUNKS],
        markers=all_opts[inputs.KEY_MARKERS],
        client_interface=all_opts[inputs.KEY_CLIENT_IFACE],
        server_interface=all_opts[inputs.KEY_SERVER_IFACE],
        local_output_directory=all_opts[inputs.KEY_ROOT_DIR],
        sut_brand=all_opts[inputs.KEY_BRAND],
        sut_hardware=all_opts[inputs.KEY_HARDWARE],
        sut_software=all_opts[inputs.KEY_SOFTWARE],
        radius_port=all_opts[inputs.KEY_RADIUS_PORT],
    )
    return test_config

def read_config_file(filename: str) -> TestConfig:
    """Read test configuration from a YAML file"""
    with open(filename, "r", encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return TestConfig(**config)


def setup_logging(debug):
    if debug:
        logging.basicConfig(
            level=logging.DEBUG, format="%(asctime)s - %(levelname)s: %(message)s"
        )
    else:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


def create_dir_if_not_exists(directory):
    if not os.path.exists(directory):
        logging.info(f"Creating directory {directory}")
        os.makedirs(directory)

#check if interfaces exist
def check_interfaces_exist(self, *args):
    """Check if the specified network interfaces exist"""
    for iface in args:
        try:
            subprocess.run(
                ["ip", "link", "show", iface],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            self.logger.error(f"Interface {iface} does not exist.")
            return False
    return True

class TestSetup:
    """Class that contains common methods and attributes for all tests."""

    def __init__(self, test_config: TestConfig, logger: logging.Logger, debug=False):
        self.config = test_config
        self.debug = debug
        self.logger = logger
        self.logs_dir = self.config.logs_dir
        self.pcap_dir = self.config.pcap_dir
        self.root_dir = self.config.local_output_directory
        self.__create_dirs()
        self.__initialize_proc_vars()
        logging.debug("Test configuration: %s", self.config.pretty_print)
        if not check_interfaces_exist(self, self.config.client_interface, self.config.server_interface):
            sys.exit()

    def __create_dirs(self):
        """Create subdirectories for logs, pcap, configs, and reports"""
        for dir in [
            self.logs_dir,
            self.pcap_dir,
            self.config.configs_dir,
            self.config.reports_dir,
        ]:
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
        self.radius_tcpdump_log = files.get_tcpdump_log_filename(
            test_name, self.root_dir
        )
        self.freeradius_log = files.get_freeradius_log_filename(
            self.config.test_name, self.root_dir
        )
        self.radius_pcap_location = files.get_pcap_filename(
            self.config.test_name, self.root_dir
        )
        self.wpa_supplicant_log = files.get_wpasupplicant_log_filename(
            self.config.test_name, self.root_dir
        )

    def __initialize_proc_objs(self):
        """Initialize process objects for the test"""
        self.__initialize_output_locations()
        port = int(self.config.radius_port)
        _filter = f"port {port} or port {port + 1}"
        self.radius_tcpdump = procs.TCPDump(
            interface=self.config.server_interface,
            pcap_location=self.radius_pcap_location,
            log_location=self.radius_tcpdump_log,
            _filter=_filter,
        )
        self.wpasupplicant = procs.WpaSupplicant(
            interface=self.config.client_interface,
            log_location=self.wpa_supplicant_log,
            ssid=self.config.ssid,
        )
        self.freeradius = procs.FreeRADIUS(
            log_location=self.freeradius_log, debug=self.debug, port=port
        )

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


def generate_pcap(test_config: TestConfig, logger: logging.Logger, debug=False):
    """Run end-to-end test and generate PCAP + PCAP metadata."""

    test = TestSetup(test_config, debug=debug, logger=logger)
    chunks = test_config.chunks

    # Start test for PCAP generation.
    begin = test.start()
    time.sleep(2)

    # Create TCP server
    data_server = TCPServer(
        test_config.data_server_ip,
        test_config.data_server_port,
        test_config.data_server_listen_port,
        test_config.chunk_size,
        test_config.chunks,
        test_config.client_interface,
    )

    # Start data transfer.
    logger.info(f"pulling {chunks} chunks")
    start_time = datetime.now()
    begin_data_transfer = time.perf_counter()
    if test_config.download_chunks:
        data_server.start(download=True)
        usage_download = data_server.transfer_data(logger=logger)
        logger.debug(f"usage_download: {usage_download}")
    else:
        usage_download = None

    if test_config.upload_chunks:
        if test_config.download_chunks:
            logger.info("sleeping for 10 seconds")
            time.sleep(10)
        data_server.start(download=False)
        usage_upload = data_server.transfer_data(logger=logger)
        logger.debug(f"usage_upload: {usage_upload}")
    else:
        usage_upload = None

    # Data transfer completed, stop test.
    end = time.perf_counter()
    end_time = datetime.now()
    session_duration = int(end - begin)
    data_transfer_duration = end - begin_data_transfer
    logger.info(f"Data transfer completed in {data_transfer_duration:.2f} seconds")

    time.sleep(10)
    test.stop()

    # Write test metadata to file.
    filename_withdir = files.get_metadata_filename(
        test_config.test_name, test_config.local_output_directory
    )
    test_metadata = Metadata(
        username=test.username,
        session_duration=session_duration,
        chunk_size=str(test_config.chunk_size),
        chunks=str(chunks),
        sut_brand=test_config.sut_brand,
        sut_hardware=test_config.sut_hardware,
        sut_software=test_config.sut_software,
        start_time=start_time,
        uploaded=test_config.upload_chunks,
        usage_upload=usage_upload,
        downloaded=test_config.download_chunks,
        usage_download=usage_download,
        end_time=end_time,
        radius_port=test_config.radius_port,
    )
    test_metadata_dict = test_metadata.get_dict()

    logger.info(f'Writing metadata to file "{filename_withdir}"')
    with open(filename_withdir, "w", encoding='utf-8') as f:
        json.dump(test_metadata_dict, f)
    logger.info(f"Test {test_config.test_name} completed")

