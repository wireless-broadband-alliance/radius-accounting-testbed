"""Test data transfer functionality using TCPServer."""

import logging
import pytest
from src.data_transfer import TCPServer

CHUNK_SIZE = 1000
CHUNKS = 1000
CLIENT_IFACE = "lo"
SLEEP_TIME = 10
TEST_TOLERANCE = 0.05


@pytest.fixture(scope="module", autouse=True)
def data_server():
    """Create a TCP server for testing."""
    server = TCPServer(
        dst_host="127.0.0.1",
        dst_port=8000,
        listen_port=8000,
        chunk_size=CHUNK_SIZE,
        chunks=CHUNKS,
        client_iface=CLIENT_IFACE,
    )
    return server


def test_download(data_server):
    """Test the download functionality of the TCP server."""
    logging.info("Starting download test")
    data_server.start(download=True)
    usage = data_server.transfer_data()
    lower = CHUNK_SIZE*CHUNKS
    upper = CHUNK_SIZE * CHUNKS * (1 + TEST_TOLERANCE)
    assert usage.bytes_recv > lower
    assert usage.bytes_recv < upper


def test_upload(data_server):
    """Test the upload functionality of the TCP server."""
    logging.info("Starting upload test")
    data_server.start(download=False)
    usage = data_server.transfer_data()
    lower = CHUNK_SIZE*CHUNKS
    upper = CHUNK_SIZE * CHUNKS * (1 + TEST_TOLERANCE)
    assert usage.bytes_sent > lower
    assert usage.bytes_sent < upper
