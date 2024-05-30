import logging
import argparse
import time

from raatestbed.data_transfer import get_data_chunk
from raatestbed.test_setup import TestSetup

from raatestbed.test_setup import DEFAULT_LOGS_DIR
from raatestbed.test_setup import DEFAULT_PCAP_DIR
from raatestbed.test_setup import DEFAULT_CHUNK_SIZE
from raatestbed.test_setup import DEFAULT_SSID
from raatestbed.test_setup import DEFAULT_WIRELESS_IFACE
from raatestbed.test_setup import DEFAULT_WIRED_IFACE


# TODO: too many arguments, maybe use a config file
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("test_name", type=str, help="Name of the test to run")
    parser.add_argument(
        "data_server_ip", type=str, help="IP of the server to get data from"
    )
    parser.add_argument(
        "data_server_port", type=int, help="Port of the server to get data from"
    )
    parser.add_argument(
        "--interface", type=str, default="wlan0", help="Interface used to get data from"
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--data_server_listen_port", type=str, default=8000)
    parser.add_argument("--logs_dir", type=str, default=DEFAULT_LOGS_DIR)
    parser.add_argument("--pcap_dir", type=str, default=DEFAULT_PCAP_DIR)
    parser.add_argument("--chunk_size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--chunks", type=int, default=1)
    parser.add_argument("--ssid", type=str, default=DEFAULT_SSID)
    parser.add_argument(
        "--wireless_interface", type=str, default=DEFAULT_WIRELESS_IFACE
    )
    parser.add_argument("--wired_interface", type=str, default=DEFAULT_WIRED_IFACE)
    return parser.parse_args()


def setup_logging(debug):
    if debug:
        logging.basicConfig(
            level=logging.DEBUG, format="%(asctime)s - %(levelname)s: %(message)s"
        )
    else:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


def main():
    args_orig = parse_args()
    args = vars(parse_args())
    setup_logging(args_orig.debug)

    # TODO: Add user interface to select values

    test = TestSetup(
        test_name=args["test_name"],
        ssid=args["ssid"],
        data_server_port=args["data_server_listen_port"],
        data_chunk_size=args["chunk_size"],
        logs_dir=args["logs_dir"],
        pcap_dir=args["pcap_dir"],
        debug=args["debug"],
        wireless_interface=args["wireless_interface"],
        wired_interface=args["wired_interface"],
    )
    test.start()
    time.sleep(2)
    chunks = args["chunks"]
    logging.info(f"pulling {chunks} chunks")
    begin = time.perf_counter()
    for num in range(chunks):
        logging.info(f"pulling chunk {num+1} of {chunks}")
        get_data_chunk(
            server_host=args["data_server_ip"],
            server_port=args["data_server_port"],
            chunk_size=args["chunk_size"],
            iface=args["interface"],
        )
    end = time.perf_counter()
    logging.info(f"Download completed in {end - begin:.2f} seconds")
    test.stop()


if __name__ == "__main__":
    main()
