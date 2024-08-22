import argparse
import raatestbed.test_setup as ts
import logging
import pytest
import yaml
from raatests.extra_funcs import get_metadata

from raatestbed.test_setup import DEFAULT_ROOT_DIR
from raatestbed.test_setup import DEFAULT_CHUNK_SIZE
from raatestbed.test_setup import DEFAULT_SSID
from raatestbed.test_setup import DEFAULT_WIRELESS_IFACE
from raatestbed.test_setup import DEFAULT_WIRED_IFACE
from raatestbed.test_setup import DEFAULT_DATA_SERVER_LISTEN_PORT
from raatestbed.test_setup import DEFAULT_CHUNKS
from raatestbed.test_setup import DEFAULT_SUT
from raatestbed.test_setup import DEFAULT_GENERATE_PCAP
from raatestbed.test_setup import DEFAULT_GENERATE_REPORT

# TODO: dynamically generate tags/markers from pytest
TEST_TAGS = ["core", "core_upload", "core_download", "openroaming"]


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
        "--config", type=str, help="Optional config file to get input from"
    )
    parser.add_argument(
        "--markers",
        type=str,
        default=None,
        help="Test Markers: core, core-upload, core-download, openroaming (default)",
    )
    parser.add_argument(
        "--interface",
        type=str,
        default=None,
        help=f"Interface used to get data from (default: {DEFAULT_WIRELESS_IFACE})",
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "--data_server_listen_port",
        type=str,
        default=None,
        help=f"default: {DEFAULT_DATA_SERVER_LISTEN_PORT}",
    )
    parser.add_argument(
        "--local_output_directory",
        type=str,
        default=None,
        help=f"default: {DEFAULT_ROOT_DIR}",
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        default=None,
        help=f"default: {DEFAULT_CHUNK_SIZE}",
    )
    parser.add_argument(
        "--chunks",
        type=int,
        default=None,
        help=f"Number of chunks to pull, default: {DEFAULT_CHUNKS}",
    )
    parser.add_argument(
        "--ssid", type=str, default=None, help=f"default: {DEFAULT_SSID}"
    )
    parser.add_argument("--sut_firmware", type=str, default=None, help="SUT firmware")
    parser.add_argument("--sut_make", type=str, default=None, help="SUT make")
    parser.add_argument("--sut_model", type=str, default=None, help="SUT model")
    parser.add_argument(
        "--client_interface",
        type=str,
        default=None,
        help=f"default: {DEFAULT_WIRELESS_IFACE}",
    )
    parser.add_argument(
        "--server_interface",
        type=str,
        default=None,
        help=f"default: {DEFAULT_WIRED_IFACE}",
    )
    parser.add_argument("--no_pcap", action="store_true", help="Skip PCAP generation")
    parser.add_argument(
        "--no_test", action="store_true", help="Skip test case execution"
    )
    return parser.parse_args()


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
    markers = " or ".join(config.markers)
    markers_log = " ".join(config.markers)
    pytest_args = ["-v", "raatests", "--test_name", test_name]
    extra_args = ["-m", markers]
    if user_wants_to_continue(f'Run test suites "{markers_log}"'):
        pytest.main(pytest_args + extra_args)


def get_input_value(cliarg, default_value, configarg=None):
    """Logic to decide which value to use based on the input."""
    # Priority: CLI > Config > Default
    if cliarg:
        return cliarg
    elif configarg:
        return configarg
    else:
        return default_value


def change_marker_format(markers: str, delim=",") -> list:
    """Convert markers string to list."""
    if not markers:
        return []
    return markers.split(delim)


def get_testconfig_with_config_file(cliargs, configargs) -> ts.TestConfig:
    """Create TestConfig object with CLI args WITH config file."""
    cliargs["markers"] = change_marker_format(cliargs["markers"])
    config = ts.TestConfig(
        test_name=cliargs["test_name"],
        data_server_ip=cliargs["data_server_ip"],
        data_server_port=cliargs["data_server_port"],
        chunk_size=int(
            get_input_value(
                cliargs["chunk_size"], DEFAULT_CHUNK_SIZE, configargs["chunk_size"]
            )
        ),
        chunks=int(
            get_input_value(cliargs["chunks"], DEFAULT_CHUNK_SIZE, configargs["chunks"])
        ),
        sut_make=get_input_value(
            cliargs["sut_make"], DEFAULT_SUT, configargs["sut_make"]
        ),
        sut_model=get_input_value(
            cliargs["sut_model"], DEFAULT_SUT, configargs["sut_model"]
        ),
        sut_firmware=get_input_value(
            cliargs["sut_firmware"], DEFAULT_SUT, configargs["sut_firmware"]
        ),
        data_server_listen_port=int(
            get_input_value(
                cliargs["data_server_listen_port"],
                DEFAULT_DATA_SERVER_LISTEN_PORT,
                configargs["data_server_listen_port"],
            )
        ),
        ssid=get_input_value(cliargs["ssid"], DEFAULT_SSID, configargs["ssid"]),
        generate_pcap=get_input_value(
            not cliargs["no_pcap"],
            DEFAULT_GENERATE_PCAP,
            configargs["generate_pcap"],
        ),
        generate_report=get_input_value(
            not cliargs["no_test"],
            DEFAULT_GENERATE_REPORT,
            configargs["generate_report"],
        ),
        markers=get_input_value(cliargs["markers"], configargs["markers"], TEST_TAGS),
        client_interface=get_input_value(
            cliargs["client_interface"],
            DEFAULT_WIRELESS_IFACE,
            configargs["client_interface"],
        ),
        server_interface=get_input_value(
            cliargs["server_interface"],
            DEFAULT_WIRED_IFACE,
            configargs["server_interface"],
        ),
        local_output_directory=get_input_value(
            cliargs["local_output_directory"],
            DEFAULT_ROOT_DIR,
            configargs["local_output_directory"],
        ),
    )
    return config


def get_testconfig_without_config_file(cliargs) -> ts.TestConfig:
    """Create TestConfig object with CLI args WITHOUT config file."""
    cliargs["markers"] = change_marker_format(cliargs["markers"])
    config = ts.TestConfig(
        test_name=cliargs["test_name"],
        data_server_ip=cliargs["data_server_ip"],
        data_server_port=cliargs["data_server_port"],
        chunk_size=int(get_input_value(cliargs["chunk_size"], DEFAULT_CHUNK_SIZE)),
        chunks=int(get_input_value(cliargs["chunks"], DEFAULT_CHUNKS)),
        data_server_listen_port=int(
            get_input_value(
                cliargs["data_server_listen_port"], DEFAULT_DATA_SERVER_LISTEN_PORT
            )
        ),
        ssid=get_input_value(cliargs["ssid"], DEFAULT_SSID),
        generate_pcap=get_input_value(not cliargs["no_pcap"], DEFAULT_GENERATE_PCAP),
        generate_report=get_input_value(
            not cliargs["no_test"], DEFAULT_GENERATE_REPORT
        ),
        markers=get_input_value(cliargs["markers"], TEST_TAGS),
        client_interface=get_input_value(
            cliargs["client_interface"], DEFAULT_WIRELESS_IFACE
        ),
        server_interface=get_input_value(
            cliargs["server_interface"], DEFAULT_WIRED_IFACE
        ),
        local_output_directory=get_input_value(
            cliargs["local_output_directory"], DEFAULT_ROOT_DIR
        ),
        sut_make=get_input_value(cliargs["sut_make"], DEFAULT_SUT),
        sut_model=get_input_value(cliargs["sut_model"], DEFAULT_SUT),
        sut_firmware=get_input_value(cliargs["sut_firmware"], DEFAULT_SUT),
    )
    return config


def main():
    # Parse command line arguments and set up logging.
    cliargs_orig = parse_cliargs()
    cliargs = vars(cliargs_orig)
    logger = logging.getLogger(__name__)
    ts.setup_logging(cliargs_orig.debug)

    # Create TestConfig object using CLI args WITH config file
    if cliargs["config"]:
        # config_file = ts.read_config_file(cliargs["config"])
        config_file = cliargs["config"]
        with open(config_file, "r") as file:
            configargs = yaml.safe_load(file)
        config = get_testconfig_with_config_file(cliargs, configargs)

    # Create TestConfig object using CLI args WITHOUT config file
    else:
        config = get_testconfig_without_config_file(cliargs)
    config.write_yaml()

    # Generate PCAP.
    if config.generate_pcap:
        ts.generate_pcap(config, logger)

    # Execute tests.
    if config.generate_report:
        execute_test_cases(config, logger)


if __name__ == "__main__":
    main()
