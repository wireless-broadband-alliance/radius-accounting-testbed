import time
import os
import logging
import psutil
import raatestbed.processes as procs
from raatestbed.data_transfer import TCPServer, get_data_chunk


DEFAULT_ROOT_DIR = "/usr/local/raa"
DEFAULT_LOGS_DIR = os.path.join(DEFAULT_ROOT_DIR, "logs")
DEFAULT_PCAP_DIR = os.path.join(DEFAULT_ROOT_DIR, "pcap")
DEFAULT_WIRELESS_IFACE = "wlan0"
DEFAULT_WIRED_IFACE = "eth0"
DEFAULT_CHUNK_SIZE = 1024**2
DEFAULT_SSID = "raatest"


def create_dir_if_not_exists(directory):
    """Check if network interface has IP"""
    if not os.path.exists(directory):
        logging.info(f"Creating directory {directory}")
        os.makedirs(directory)


class TestSetup:
    """Class that contains common methods and attributes for all tests."""

    def __init__(
        self,
        test_name,
        ssid=DEFAULT_SSID,
        wireless_interface=DEFAULT_WIRELESS_IFACE,
        wired_interface=DEFAULT_WIRED_IFACE,
        data_server_port=8000,
        debug=False,
        data_chunk_size=DEFAULT_CHUNK_SIZE,
        logs_dir=DEFAULT_LOGS_DIR,
        pcap_dir=DEFAULT_PCAP_DIR,
    ):
        self.test_name = test_name
        self.ssid = ssid
        self.wireless_interface = wireless_interface
        self.wired_interface = wired_interface
        self.data_server_port = data_server_port
        self.data_chunk_size = data_chunk_size
        self.logs_dir = logs_dir
        self.pcap_dir = pcap_dir
        self.debug = debug
        self.__initialize_proc_vars()

    def __initialize_proc_vars(self):
        """Initialize all processes variables"""
        self.freeradius = None
        self.wpasupplicant = None
        self.data_server = None
        self.radius_tcpdump = None
        self.proc_objs = None

    def __check_for_ip(self):
        """Check if network interface has IP"""
        addrs = psutil.net_if_addrs()
        if self.wireless_interface not in addrs:
            return False
        if not addrs[self.wireless_interface]:
            return False
        return True

    def __initialize_output_locations(self):
        """Initialize output locations for logs and pcap files"""
        test_name = self.test_name
        create_dir_if_not_exists(self.logs_dir)
        create_dir_if_not_exists(self.pcap_dir)
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
            interface=self.wired_interface,
            pcap_location=self.radius_pcap_location,
            log_location=self.radius_tcpdump_log,
        )
        self.wpasupplicant = procs.WpaSupplicant(
            interface=self.wireless_interface,
            log_location=self.wpa_supplicant_log,
            ssid=self.ssid,
        )
        self.freeradius = procs.FreeRADIUS(
            log_location=self.freeradius_log, debug=self.debug
        )
        self.data_server = TCPServer(self.data_server_port, self.data_chunk_size)
        self.proc_objs = (
            self.radius_tcpdump,
            self.wpasupplicant,
            self.freeradius,
            self.data_server,
        )

    def start(self, wait_for_ip=True, extra_wait_time=3):
        """Start processes"""
        self.stop()
        self.__initialize_proc_objs()
        assert self.proc_objs is not None
        logging.info(f'Starting test "{self.test_name}"...')
        for proc in self.proc_objs:
            assert proc is not None
            proc.start()
        if wait_for_ip:
            # Block until wireless interface has IP
            logging.info(f"Waiting for IP on {self.wireless_interface}...")
            while not self.__check_for_ip():
                pass
        time.sleep(extra_wait_time)  # wait for network to settle

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


# TODO: Simplify arguments and upload+download calls
def get_chunks(
    test_name,
    data_server_ip,
    data_server_port,
    iface,
    data_server_listen_port=None,
    chunks=1,
    ssid="raatest",
    data_chunk_size=DEFAULT_CHUNK_SIZE,
    logs_dir=DEFAULT_LOGS_DIR,
    pcap_dir=DEFAULT_PCAP_DIR,
    debug=False,
):
    if data_server_listen_port is None:
        data_server_listen_port = data_server_port
    test = TestSetup(
        test_name=test_name,
        ssid=ssid,
        data_server_port=data_server_listen_port,
        data_chunk_size=data_chunk_size,
        logs_dir=logs_dir,
        pcap_dir=pcap_dir,
        debug=debug,
    )
    test.start()
    time.sleep(2)
    logging.info(f"pulling {chunks} chunks")
    begin = time.perf_counter()
    for num in range(chunks):
        logging.info(f"pulling chunk {num+1} of {chunks}")
        get_data_chunk(
            server_host=data_server_ip,
            server_port=data_server_port,
            chunk_size=data_chunk_size,
            iface=iface,
        )
    end = time.perf_counter()
    logging.info(f"Download completed in {end - begin:.2f} seconds")
    test.stop()
