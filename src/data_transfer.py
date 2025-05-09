"""Contains imports for data transfer between two hosts."""

import socket
import logging
import threading
import time
from dataclasses import dataclass
import netifaces
import psutil


@dataclass
class UsageCounter:
    """Store usage counter during data transfer."""

    packets_sent: int
    packets_recv: int
    bytes_sent: int
    bytes_recv: int
    interface: int

    def to_dict(self):
        """Convert the UsageCounter object to a dictionary for easier interpretation."""
        return {
            "packets_sent": self.packets_sent,
            "packets_recv": self.packets_recv,
            "bytes_sent": self.bytes_sent,
            "bytes_recv": self.bytes_recv,
            "interface": self.interface,
        }

    def __sub__(self, other):
        """Subtract another UsageCounter object from this one."""
        return UsageCounter(
            self.packets_sent - other.packets_sent,
            self.packets_recv - other.packets_recv,
            self.bytes_sent - other.bytes_sent,
            self.bytes_recv - other.bytes_recv,
            self.interface,
        )

    def __str__(self):
        return f"packets sent: {self.packets_sent}\npackets recv: {self.packets_recv}\nbytes sent: {self.bytes_sent}\nbytes recv: {self.bytes_recv}\ninterface: {self.interface}"


def get_interface_ip(interface_name):
    """Get the IP address of a network interface."""
    try:
        # Get the IP address for the specified network interface
        addresses = netifaces.ifaddresses(interface_name)
        ipv4_address = addresses[netifaces.AF_INET][0]["addr"]
        return ipv4_address
    except (KeyError, ValueError) as e:
        logging.error("Error: %s", e)
        raise e

def print_progress_bool(expected_bytes, count) -> bool:
    """Print progress of data transfer if expected_bytes is greater than 1000000000."""
    if expected_bytes > 1e9 and count % 1000 != 0:
        return False 
    return True 

class TCPServer:
    """Server that listens for incoming connections and sends random data to clients."""

    def __init__(
        self,
        dst_host,
        dst_port,
        listen_port,
        chunk_size,
        chunks,
        client_iface=None,
    ):
        self.listen_port = listen_port
        self.dst_host = dst_host
        self.dst_port = dst_port
        self.client_iface = client_iface
        self.chunk_size = chunk_size
        self.chunks = chunks
        self.server_thread = None
        self.ready_for_conns = threading.Event()
        self.download = None

    def __tcp_server(self, download=True):
        """Server that listens for incoming connections and sends or receives 
        random data to clients."""
        mode = "download" if download else "upload"
        logging.info("Starting TCP data server (mode=%s)...", mode)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                server.bind(("0.0.0.0", self.listen_port))
            except OSError as e:
                logging.debug(
                    "Not ready to bind: %s, sleeping for 120 seconds and retrying", e
                )
                time.sleep(120)
                server.bind(("0.0.0.0", self.listen_port))

            server.listen()
            self.ready_for_conns.set()

            client_sock, client_addr = server.accept()
            logging.debug("Client connected from %s", client_addr)

            with client_sock:
                if download:
                    logging.debug("Download mode selected")
                    self.__tx_data_chunks(logging, client_sock)
                else:
                    logging.info("Upload mode selected")
                    self.__rx_data_chunks(logging, client_sock, "Server received")
            time.sleep(3)
            logging.info("Client connection closed")
        logging.info("Server closed")
        self.ready_for_conns.clear()

    def tcp_server_upload(self):
        """Start the TCP server in upload mode."""
        self.__tcp_server(download=False)

    def tcp_server_download(self):
        """Start the TCP server in download mode."""
        self.__tcp_server(download=True)

    def start(self, download=True):
        """Start the TCP server in upload or download mode."""
        if download:
            #Download mode
            self.download = True
            thread = threading.Thread(target=self.tcp_server_download)
        else:
            #Upload mode
            self.download = False
            thread = threading.Thread(target=self.tcp_server_upload)
        thread.start()
        while not self.ready_for_conns.is_set():
            pass
        logging.info("TCP data server started")

    def __connect_socket_with_interface(self):
        """Connect to server and return socket binded to interface."""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        iface = self.client_iface
        if iface:
            source_ip = get_interface_ip(iface)
            logging.debug("Binding to interface %s with IP %s", iface, source_ip)
            client_socket.setsockopt(socket.SOL_SOCKET, 25, iface.encode())
            client_socket.bind((source_ip, 0))
        try:
            client_socket.connect((self.dst_host, self.dst_port))
        except socket.gaierror as e:
            logging.error("Error: %s", e)
        return client_socket

    def __tx_data_chunks(self, logger, sock, verb=None):
        """Behavior for one side to send data chunks to other side."""
        file_path = "/dev/random"
        with open(file_path, "rb") as file:
            data = file.read(self.chunk_size)
        usage_start = get_usage_data(self.client_iface)
        count = 0
        expected_bytes = self.chunks * self.chunk_size
        while True:
            count += 1
            try:
                sock.sendall(data)
            except BrokenPipeError:
                break
            except ConnectionResetError:
                break
            cur_usage = get_usage_data(self.client_iface) - usage_start
            if verb and (print_progress_bool(expected_bytes, count)):
                logger.info(f"Iface {cur_usage.interface}: {cur_usage.bytes_sent}")
                logger.info(f"{verb} data chunk {count + 1}")

    def __rx_data_chunks(self, logger, sock, verb=None):
        """Behavior for one side to receive data chunks from other side."""
        expected_bytes = self.chunks * self.chunk_size
        count = 0
        byte_count = 0
        while True:
            try:
                bytes_to_pull = min(expected_bytes - byte_count, self.chunk_size)
                actual_len = len(sock.recv(bytes_to_pull))
            except BrokenPipeError:
                break
            except ConnectionResetError:
                break
            if actual_len != 0:
                count += 1
                byte_count += actual_len
                if verb and print_progress_bool(expected_bytes, count):
                    logger.info(
                        f"{verb} chunk {count} of size {actual_len}, total bytes: {byte_count} of {expected_bytes}"
                    )
                if byte_count >= expected_bytes:
                    break
            else:
                break

    def __download_data_chunks(self, logger):
        """Client that connects to this server and receives data from it."""
        client = self.__connect_socket_with_interface()
        with client:
            self.__rx_data_chunks(logger, client, verb="Client downloaded")

    def __upload_data_chunks(self, logger):
        """Client that connects to this server and sends data to it."""
        client = self.__connect_socket_with_interface()
        with client:
            self.__tx_data_chunks(logger, client)

    def transfer_data(self, logger=None) -> UsageCounter:
        """Decide whether to download or upload data chunks based on self.download flag."""
        if logger is None:
            logger = logging.getLogger(__name__)
        # Get first network interface if not specified
        if not self.client_iface:
            network_interface = list(netifaces.interfaces())[0]
        else:
            network_interface = self.client_iface
        usage_before = get_usage_data(network_interface)
        if self.download:
            self.__download_data_chunks(logger)
        else:
            self.__upload_data_chunks(logger)
        time.sleep(1)
        return get_usage_data(network_interface) - usage_before


def get_usage_data(client_iface):
    """Return usage counter data."""
    network_counters = psutil.net_io_counters(pernic=True)
    packets_tx = network_counters[client_iface].packets_sent
    packets_rx = network_counters[client_iface].packets_recv
    bytes_tx = network_counters[client_iface].bytes_sent
    bytes_rx = network_counters[client_iface].bytes_recv
    return UsageCounter(packets_tx, packets_rx, bytes_tx, bytes_rx, client_iface)
