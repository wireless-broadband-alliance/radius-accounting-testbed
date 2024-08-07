import argparse
import raatestbed.test_setup as ts
import logging
import pytest
from raatests.extra_funcs import get_metadata

from raatestbed.test_setup import DEFAULT_ROOT_DIR
from raatestbed.test_setup import DEFAULT_CHUNK_SIZE
from raatestbed.test_setup import DEFAULT_SSID
from raatestbed.test_setup import DEFAULT_WIRELESS_IFACE
from raatestbed.test_setup import DEFAULT_WIRED_IFACE



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
        "--markers",
        type=str,
        default="core",
        help=f"Test Markers: core, core-upload, core-download, openroaming (default)"
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
        "--root_dir",
        type=str,
        default=DEFAULT_ROOT_DIR,
        help=f"default: {DEFAULT_ROOT_DIR}",
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
        "--sut_firmware", type=str, default="", help=f"SUT firmware"
    )
    parser.add_argument(
        "--sut_make", type=str, default="", help=f"SUT make"
    )
    parser.add_argument(
        "--sut_model", type=str, default="", help=f"SUT model"
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


def execute_test_cases(config: ts.TestConfig, logger: logging.Logger):
    """Run tests against PCAP."""
    test_name = config.test_name
    metadata = get_metadata(test_name, config.pcap_dir)
    logger.info(f'\n\nMetadata for "{test_name}":\n{metadata.pretty_print_format()}\n')
    markers_txt, markers = select_markers()
    pytest_args = ["-v", "raatests", "--test_name", test_name]
    extra_args = ["-m", markers]
    if user_wants_to_continue(f'Running test suites "{markers_txt}"'):
        pytest.main(pytest_args + extra_args)


def main():
    # Parse command line arguments and set up logging.
    cliargs_orig = parse_cliargs()
    cliargs = vars(cliargs_orig)
    logger = logging.getLogger(__name__)
    ts.setup_logging(cliargs_orig.debug)
    markers = cliargs["markers"].split(",")
    config = ts.TestConfig(
        test_name=cliargs["test_name"],
        data_server_ip=cliargs["data_server_ip"],
        data_server_port=cliargs["data_server_port"],
        chunk_size=cliargs["chunk_size"],
        chunks=cliargs["chunks"],
        sut_make=cliargs["sut_make"],
        sut_model=cliargs["sut_model"],
        sut_firmware=cliargs["sut_firmware"],
        data_server_listen_port=cliargs["data_server_listen_port"],
        ssid=cliargs["ssid"],
        generate_pcap=not cliargs["no_pcap"],
        generate_report=not cliargs["no_test"],
        markers=markers,
        client_interface = cliargs["wireless_interface"],
        server_interface = cliargs["wired_interface"],
        local_output_directory=cliargs["root_dir"],
    )
    config.write_yaml()

    # Generate PCAP.
    if not cliargs["no_pcap"]:
        ts.generate_pcap(config, logger)

    # Execute tests.
    if not cliargs["no_test"]:
        execute_test_cases(config, logger)


if __name__ == "__main__":
    main()
