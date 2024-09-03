"""Contains test setup-related imports."""

import time
import os
import logging
import subprocess
import yaml
import json
from datetime import datetime
from typing import List
from dataclasses import dataclass

import raatestbed.processes as procs
import raatestbed.files as files
from raatestbed.data_transfer import TCPServer, get_data_chunk
from raatestbed.metadata import Metadata


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

    def write_yaml(self):
        """Write test configuration to a YAML file"""
        config = files.get_config_filename(self.test_name, self.local_output_directory)
        logging.info(f"Writing test configuration to {config}")
        with open(config, "w") as file:
            yaml.dump(self.__to_dict__(), file)


def read_config_file(filename: str) -> TestConfig:
    """Read test configuration from a YAML file"""
    with open(filename, "r") as file:
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
        self.data_server = TCPServer(
            self.config.data_server_listen_port, self.config.chunk_size
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


def generate_pcap(test_config: TestConfig, logger: logging.Logger, debug=False):
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
            iface=test_config.client_interface,
        )

    # Data transfer completed, stop test.
    end = time.perf_counter()
    end_time = datetime.now()
    session_duration = int(end - begin)
    data_transfer_duration = end - begin_data_transfer
    logger.info(f"Download completed in {data_transfer_duration:.2f} seconds")
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
        end_time=end_time,
    )
    test_metadata_dict = test_metadata.get_dict()

    logger.info(f'Writing metadata to file "{filename_withdir}"')
    with open(filename_withdir, "w") as f:
        json.dump(test_metadata_dict, f)
