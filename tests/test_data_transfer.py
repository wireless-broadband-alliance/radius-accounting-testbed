from src.data_transfer import TCPServer
import logging
import time
import pytest

chunk_size = 1000
chunks = 1000
client_iface = "lo"
sleep_time = 10
test_tolerance = 0.05


@pytest.fixture(scope="module", autouse=True)
def data_server():
    # Create TCP server
    data_server = TCPServer(
        dst_host="127.0.0.1",
        dst_port=8000,
        listen_port=8000,
        chunk_size=chunk_size,
        chunks=chunks,
        client_iface=client_iface,
    )
    return data_server


def test_download(data_server):
    time.sleep(30)
    logging.info("Starting download test")
    data_server.start(download=True)
    usage = data_server.transfer_data()
    assert usage.bytes_recv > chunk_size * chunks
    assert usage.bytes_recv < chunk_size * chunks * (1 + test_tolerance)


def test_upload(data_server):
    time.sleep(30)
    logging.info("Starting upload test")
    data_server.start(download=False)
    usage = data_server.transfer_data()
    assert usage.bytes_sent > chunk_size * chunks
    assert usage.bytes_sent < chunk_size * chunks * (1 + test_tolerance)
