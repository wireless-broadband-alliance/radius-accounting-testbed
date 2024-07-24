import logging
import argparse
import time
import json
import os
import pytest
from datetime import datetime

from raatestbed.data_transfer import get_data_chunk
from raatestbed.test_setup import TestSetup

from raatestbed.test_setup import DEFAULT_LOGS_DIR
from raatestbed.test_setup import DEFAULT_PCAP_DIR
from raatestbed.test_setup import DEFAULT_CHUNK_SIZE
from raatestbed.test_setup import DEFAULT_SSID
from raatestbed.test_setup import DEFAULT_WIRELESS_IFACE
from raatestbed.test_setup import DEFAULT_WIRED_IFACE

from raatests.extra_funcs import get_metadata, Metadata


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
        "--interface",
        type=str,
        default=DEFAULT_WIRELESS_IFACE,
        help=f"Interface used to get data from (default: {DEFAULT_WIRELESS_IFACE})",
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "--data_server_listen_port", type=str, default=8000, help="default: 8000"
    )
    parser.add_argument(
        "--logs_dir",
        type=str,
        default=DEFAULT_LOGS_DIR,
        help=f"default: {DEFAULT_LOGS_DIR}",
    )
    parser.add_argument(
        "--pcap_dir",
        type=str,
        default=DEFAULT_PCAP_DIR,
        help=f"default: {DEFAULT_PCAP_DIR}",
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"default: {DEFAULT_CHUNK_SIZE}",
    )
    parser.add_argument(
        "--chunks", type=int, default=1, help="Number of chunks to pull, default: 1"
    )
    parser.add_argument(
        "--ssid", type=str, default=DEFAULT_SSID, help=f"default: {DEFAULT_SSID}"
    )
    parser.add_argument(
        "--wireless_interface",
        type=str,
        default=DEFAULT_WIRELESS_IFACE,
        help=f"default: {DEFAULT_WIRELESS_IFACE}",
    )
    parser.add_argument(
        "--wired_interface",
        type=str,
        default=DEFAULT_WIRED_IFACE,
        help=f"default: {DEFAULT_WIRED_IFACE}",
    )
    parser.add_argument("--no_pcap", action="store_true", help="Skip PCAP generation")
    parser.add_argument(
        "--no_test", action="store_true", help="Skip test case execution"
    )
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
    start_time = datetime.now()
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
    end_time = datetime.now()
    session_duration = int(end - begin)
    data_transfer_duration = end - begin_data_transfer
    logging.info(f"Download completed in {data_transfer_duration:.2f} seconds")
    test.stop()

    # Write test metadata to file.
    filename = f"{test_name}.metadata.json"
    filename_withdir = os.path.join(cliargs["pcap_dir"], filename)
    test_metadata = Metadata(
        username=test.username,
        session_duration=session_duration,
        chunk_size=chunk_size,
        chunks=chunks,
        start_time=start_time,
        end_time=end_time,
    )
    test_metadata_dict = test_metadata.get_dict()

    logging.info(f'Writing metadata to file "{filename_withdir}"')
    with open(filename_withdir, "w") as f:
        json.dump(test_metadata_dict, f)


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


def execute_test_cases(cliargs):
    """Run tests against PCAP."""
    test_name = cliargs["test_name"]
    metadata = get_metadata(test_name, cliargs["pcap_dir"])
    logging.info(f'\n\nMetadata for "{test_name}":\n{metadata.pretty_print_format()}\n')
    markers_txt, markers = select_markers()
    pytest_args = ["-v", "raatests", "--test_name", test_name]
    extra_args = ["-m", markers]
    if user_wants_to_continue(f'Running test suites "{markers_txt}"'):
        pytest.main(pytest_args + extra_args)


def main():
    # Parse command line arguments and set up logging.
    cliargs_orig = parse_cliargs()
    cliargs = vars(cliargs_orig)
    setup_logging(cliargs_orig.debug)

    # Generate PCAP.
    if not cliargs["no_pcap"]:
        generate_pcap(cliargs)

    # Execute tests.
    if not cliargs["no_test"]:
        execute_test_cases(cliargs)


if __name__ == "__main__":
    main()
