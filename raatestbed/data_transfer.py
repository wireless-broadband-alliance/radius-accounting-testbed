"""Contains imports for data transfer between two hosts."""

import socket
import logging
import threading
import netifaces
import time


def get_interface_ip(interface_name):
    try:
        # Get the IP address for the specified network interface
        addresses = netifaces.ifaddresses(interface_name)
        ipv4_address = addresses[netifaces.AF_INET][0]["addr"]
        return ipv4_address
    except (KeyError, ValueError) as e:
        logging.error(f"Error: {e}")
        raise e


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

    def __tcp_server(self, download=True):
        """Server that listens for incoming connections and sends or receives random data to clients."""
        logging.info("Starting TCP data server...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            # Do not buffer data
            server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            try:
                server.bind(("0.0.0.0", self.listen_port))
            except OSError as e:
                logging.debug(
                    f"Not ready to bind: {e}, sleeping for 30 seconds and retrying"
                )
                time.sleep(30)
                server.bind(("0.0.0.0", self.listen_port))

            server.listen()
            self.ready_for_conns.set()

            client_sock, client_addr = server.accept()
            logging.debug(f"Client connected from {client_addr}")

            with client_sock:
                if download:
                    file_path = "/dev/random"
                    logging.debug("Download mode selected")
                    with open(file_path, "rb") as file:
                        data = file.read(self.chunk_size)
                    for num in range(self.chunks):
                        logging.info(f"Sending data chunk {num+1} of {self.chunks}")
                        client_sock.sendall(data)
                else:
                    logging.info("Upload mode selected")
                    for num in range(self.chunks):
                        logging.info(f"Receiving data chunk {num+1} of {self.chunks}")
                        data = client_sock.recv(self.chunk_size)
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
            self.download = True
            thread = threading.Thread(target=self.tcp_server_download)
        else:
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
            logging.debug(f"Binding to interface {iface} with IP {source_ip}")
            client_socket.setsockopt(socket.SOL_SOCKET, 25, iface.encode())
            client_socket.bind((source_ip, 0))
        try:
            client_socket.connect((self.dst_host, self.dst_port))
        except Exception as e:
            logging.error(f"Error: {e}")
        return client_socket

    def __download_data_chunks(self):
        """Client that connects to this server and receives data from it."""
        client = self.__connect_socket_with_interface()
        with client:
            for _ in range(self.chunks):
                try:
                    client.recv(self.chunk_size)
                except BrokenPipeError:
                    break
                except ConnectionResetError:
                    break
                time.sleep(0.001)

    def __upload_data_chunks(self):
        """Client that connects to this server and sends data to it."""
        client = self.__connect_socket_with_interface()
        client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        file_path = "/dev/random"
        with open(file_path, "rb") as file:
            data = file.read(self.chunk_size)
        with client:
            for _ in range(self.chunks):
                try:
                    client.sendall(data)
                except BrokenPipeError:
                    break
                except ConnectionResetError:
                    break
                time.sleep(0.001)

    def transfer_data(self):
        """Decide whether to download or upload data chunks based on self.download flag."""
        if self.download:
            self.__download_data_chunks()
        else:
            self.__upload_data_chunks()
