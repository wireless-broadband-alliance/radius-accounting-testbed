import logging
import argparse

from raatest import get_chunks
from raatest import DEFAULT_LOGS_DIR
from raatest import DEFAULT_PCAP_DIR
from raatest import DEFAULT_CHUNK_SIZE

# TODO: Add user interface to setup and control test


# parse arguments and look for --debug flag
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--logs_dir", type=str, default=DEFAULT_LOGS_DIR)
    parser.add_argument("--pcap_dir", type=str, default=DEFAULT_PCAP_DIR)
    parser.add_argument("--chunk_size", type=int, default=DEFAULT_CHUNK_SIZE)
    return parser.parse_args()


def setup_logging(debug):
    if debug:
        logging.basicConfig(
            level=logging.DEBUG, format="%(asctime)s - %(levelname)s: %(message)s"
        )
    else:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


def main():
    args = parse_args()
    arg_vars = vars(parse_args())
    setup_logging(args.debug)

    # TODO: Add user interface to select values

    # logs_dir = arg_vars["logs_dir"]
    # pcap_dir = arg_vars["pcap_dir"]
    chunk_size = arg_vars["chunk_size"]

    # upload test
    get_chunks(
        test_name="test_ul_5gb",
        chunks=100,
        data_chunk_size=chunk_size,
        data_server_ip="192.168.123.1",
        data_server_port=8001,
        data_server_listen_port=8000,
        iface="eth0",
        ssid="raatest2",
    )


if __name__ == "__main__":
    main()
