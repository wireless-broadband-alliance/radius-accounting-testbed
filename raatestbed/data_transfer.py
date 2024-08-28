"""Contains imports for data transfer between two hosts."""

import socket
import logging
import threading
import netifaces

# TODO: Support reverse direction of data transfer (client to server). Or just listen on different address.


def get_interface_ip(interface_name):
    try:
        # Get the IP address for the specified network interface
        addresses = netifaces.ifaddresses(interface_name)
        ipv4_address = addresses[netifaces.AF_INET][0]["addr"]
        return ipv4_address
    except (KeyError, ValueError) as e:
        print(f"Error: {e}")
        raise e


def get_data_chunk(server_host, server_port, chunk_size, iface=None):
    """Client that connects to a server and receives data from it."""

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if iface:
        source_ip = get_interface_ip(iface)
        logging.debug(f"Binding to interface {iface} with IP {source_ip}")
        client_socket.setsockopt(socket.SOL_SOCKET, 25, iface.encode())
        client_socket.bind((source_ip, 0))

    try:
        client_socket.connect((server_host, server_port))
        logging.debug(f"Connected to server at {server_host}:{server_port}")
        logging.debug(
            f"Pulling {chunk_size} bytes of data from {server_host}:{server_port}"
        )
        while True:
            data = client_socket.recv(chunk_size)
            if not data:
                break

    except Exception as e:
        logging.error(f"Error: {e}")

    finally:
        client_socket.close()


class TCPServer:
    """Server that listens for incoming connections and sends random data to clients."""

    def __init__(self, port, chunk_size, host="0.0.0.0"):
        self.port = port
        self.chunk_size = chunk_size
        self.host = host
        self.server_thread = None
        self.initialize_events()

    def initialize_events(self):
        self.stop_event = threading.Event()
        self.ready_for_conns = threading.Event()

    def __tcp_server(self):
        file_path = "/dev/random"
        # Read data from file into memory.
        with open(file_path, "rb") as file:
            data = file.read(self.chunk_size)

        # Listen for incoming connections.
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen()

        logging.info(f"TCP data server is listening on {self.host}:{self.port}")
        self.ready_for_conns.set()

        while not self.stop_event.is_set():
            conn, addr = server_socket.accept()
            logging.debug(f"Connection established from {addr}")

            conn.sendall(data)
            logging.debug(f"Sent {len(data)} bytes of random data")
            conn.close()
        logging.debug("TCP data server shutting down")

    def start(self, background=True):
        logging.info("Starting TCP data server...")
        if background:
            server_thread = threading.Thread(target=self.__tcp_server)
            server_thread.start()
            self.server_thread = server_thread
        else:
            self.__tcp_server()

        # Wait for the server to be ready for connections.
        while not self.ready_for_conns.is_set():
            pass

    def stop(self):
        logging.info("Stopping TCP data server...")
        self.stop_event.set()
        # Get data chunk to stop the server, send out of lo (internally) so it won't contribute to usage in accounting.
        get_data_chunk("127.0.0.1", self.port, 1)
        self.server_thread = None
