import logging
import argparse
import time
import json
import os
import pytest

from raatestbed.data_transfer import get_data_chunk
from raatestbed.test_setup import TestSetup

from raatestbed.test_setup import DEFAULT_LOGS_DIR
from raatestbed.test_setup import DEFAULT_PCAP_DIR
from raatestbed.test_setup import DEFAULT_CHUNK_SIZE
from raatestbed.test_setup import DEFAULT_SSID
from raatestbed.test_setup import DEFAULT_WIRELESS_IFACE
from raatestbed.test_setup import DEFAULT_WIRED_IFACE

from raatests.extra_funcs import get_metadata


# TODO: too many arguments, maybe use a config file
def parse_cliargs():
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


def generate_pcap(cliargs):
    """Run end-to-end test and generate PCAP + PCAP metadata."""
    test_metadata = dict()

    # Initialize test for PCAP generation.
    test_name = cliargs["test_name"]
    test = TestSetup(
        test_name=test_name,
        ssid=cliargs["ssid"],
        data_server_port=cliargs["data_server_listen_port"],
        data_chunk_size=cliargs["chunk_size"],
        logs_dir=cliargs["logs_dir"],
        pcap_dir=cliargs["pcap_dir"],
        debug=cliargs["debug"],
        wireless_interface=cliargs["wireless_interface"],
        wired_interface=cliargs["wired_interface"],
    )

    # Start test for PCAP generation.
    begin = test.start()
    time.sleep(2)

    # Start data transfer.
    chunks = cliargs["chunks"]
    chunk_size = cliargs["chunk_size"]
    logging.info(f"pulling {chunks} chunks")
    begin_data_transfer = time.perf_counter()
    for num in range(chunks):
        logging.info(f"pulling chunk {num+1} of {chunks}")
        get_data_chunk(
            server_host=cliargs["data_server_ip"],
            server_port=cliargs["data_server_port"],
            chunk_size=cliargs["chunk_size"],
            iface=cliargs["interface"],
        )

    # Data transfer completed, stop test.
    end = time.perf_counter()
    session_duration = end - begin
    data_transfer_duration = end - begin_data_transfer
    logging.info(f"Download completed in {data_transfer_duration:.2f} seconds")
    test.stop()

    # Write test metadata to file.
    filename = f"{test_name}.metadata.json"
    filename_withdir = os.path.join(cliargs["pcap_dir"], filename)
    test_metadata["username"] = test.username
    test_metadata["session_duration"] = int(session_duration)
    test_metadata["chunk_size"] = chunk_size
    test_metadata["chunks"] = chunks
    logging.info(f'Writing metadata to file "{filename_withdir}"')
    with open(filename_withdir, "w") as f:
        json.dump(test_metadata, f)


def select_markers():
    """Select markers from a list."""

    # TODO: These should be generated dynamically
    options_mapping = {
        "1": "core",
        "2": "core_download",
        "3": "core_upload",
        "4": "openroaming",
    }
    print("\nSelect tests suite(s) from the list:")
    for key, value in options_mapping.items():
        print(f"{key}) {value}")
    print("")

    selected_options = []
    user_input = input("Enter your options (comma-separated numbers): ")
    selected_options = [
        options_mapping.get(choice.strip(), "") for choice in user_input.split(",")
    ]
    selected_options = [option for option in selected_options if option]

    return ", ".join(selected_options), " or ".join(selected_options)


def user_wants_to_continue(prompt_message):
    user_input = input(f"{prompt_message} (yes/no): ").strip().lower()

    if user_input == "yes":
        return True
    elif user_input == "no":
        return False
    else:
        print("Invalid input. Please enter 'yes' or 'no'.")
        return user_wants_to_continue(prompt_message)


def main():
    # Parse command line arguments and set up logging.
    cliargs_orig = parse_cliargs()
    cliargs = vars(parse_cliargs())
    setup_logging(cliargs_orig.debug)

    # Generate PCAP.
    generate_pcap(cliargs)

    # Run tests against PCAP.
    test_name = cliargs["test_name"]
    metadata = get_metadata(test_name, cliargs["pcap_dir"])
    logging.info(f'\n\nMetadata for "{test_name}":\n{metadata.pretty_print_format()}\n')
    markers_txt, markers = select_markers()
    pytest_args = ["-v", "raatests", "--test_name", test_name]
    extra_args = ["-m", markers]
    if user_wants_to_continue(f'Running test suites "{markers_txt}"'):
        pytest.main(pytest_args + extra_args)


if __name__ == "__main__":
    main()
