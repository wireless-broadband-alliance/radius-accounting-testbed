"""CLI for RADIUS Accounting Assurance Test Bed"""

import argparse
import raatestbed.test_setup as ts
import logging
import pytest
import yaml
import os
from raatestbed.metadata import get_metadata
import raatestbed.defaults as defaults
from typing import Union
import raatestbed.files as files


def get_possible_markers():
    """Generate markers from pytest.ini file."""
    curdir = os.path.dirname(os.path.abspath(__file__))
    pytest_ini_file = os.path.join(curdir, defaults.RELATIVE_PYTEST_INI)
    return files.get_marker_list(pytest_ini_file)


def parse_cliargs():
    markers = get_possible_markers()
    markers_str = ", ".join(markers)
    parser = argparse.ArgumentParser()
    parser.add_argument("test_name", type=str, help="Name of the test to run")
    parser.add_argument(
        "data_server_ip",
        type=str,
        default=None,
        help="IP of the server to download data from",
    )
    parser.add_argument(
        "--data_server_port",
        type=int,
        default=None,
        help=f"Port of the server to download data from (default: {defaults.DATA_SERVER_PORT})",
    )
    parser.add_argument(
        "--config", type=str, help="Optional config file to get input from"
    )
    parser.add_argument(
        "--markers",
        type=str,
        default=None,
        help=f"Test Markers: {markers_str}",
    )
    parser.add_argument(
        "--interface",
        type=str,
        default=None,
        help=f"Interface used to get data from (default: {defaults.WIRELESS_IFACE})",
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "--data_server_listen_port",
        type=str,
        default=None,
        help=f"default: {defaults.DATA_SERVER_LISTEN_PORT}",
    )
    parser.add_argument(
        "--local_output_directory",
        type=str,
        default=None,
        help=f"default: {defaults.ROOT_DIR}",
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        default=None,
        help=f"default: {defaults.CHUNK_SIZE}",
    )
    parser.add_argument(
        "--chunks",
        type=int,
        default=None,
        help=f"Number of chunks to pull, default: {defaults.CHUNKS}",
    )
    parser.add_argument(
        "--ssid", type=str, default=None, help=f"default: {defaults.SSID}"
    )
    parser.add_argument(
        "--sut_software",
        type=str,
        default=None,
        help="Software info for System Under Test (SUT)",
    )
    parser.add_argument(
        "--sut_brand", type=str, default=None, help="Brand of System Under Test (SUT)"
    )
    parser.add_argument(
        "--sut_hardware",
        type=str,
        default=None,
        help="Hardware info for System Under Test (SUT)",
    )
    parser.add_argument(
        "--client_interface",
        type=str,
        default=None,
        help=f"default: {defaults.WIRELESS_IFACE}",
    )
    parser.add_argument(
        "--server_interface",
        type=str,
        default=None,
        help=f"default: {defaults.WIRED_IFACE}",
    )
    parser.add_argument("--no_pcap", action="store_true", help="Skip PCAP generation")
    parser.add_argument(
        "--no_test", action="store_true", help="Skip test case execution"
    )
    parser.add_argument("--no_upload", action="store_true", help="Do not upload chunks")
    parser.add_argument(
        "--no_download", action="store_true", help="Do not download chunks"
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
    metadata = get_metadata(test_name, config.local_output_directory)
    logger.info(f'\n\nMetadata for "{test_name}":\n{metadata.pretty_print_format()}\n')
    markers = " or ".join(config.markers)
    markers_log = " ".join(config.markers)
    pytest_args = ["-v", "raatests", "--test_name", test_name]
    extra_args = ["-m", markers]
    logger.debug(f"\n\npytest args: {pytest_args + extra_args}\n")
    if user_wants_to_continue(f'Run test suites "{markers_log}"'):
        pytest.main(pytest_args + extra_args)


def get_input_value(default_value, cliarg=None, configarg=None):
    """Logic to decide which value to use based on the input."""
    # Priority: CLI > Config > Default
    if cliarg is not None:
        return cliarg
    elif configarg is not None:
        return configarg
    else:
        return default_value


def change_marker_format(markers: str, delim=",") -> Union[list, None]:
    """Convert markers string to list."""
    possible_delims = [",", ";", " "]
    for delim in possible_delims:
        if delim in markers:
            break
    new_markers = markers.split(delim)
    return [marker.strip() for marker in new_markers]


def get_testconfig(cliargs, configargs) -> ts.TestConfig:
    """Create TestConfig object with CLI + config args"""

    possible_markers = get_possible_markers()

    # Based on the input from CLI and config file, decide the values for TestConfig
    cliargs["markers"] = change_marker_format(cliargs["markers"])

    # Decide if we need to upload/download chunks based on the data server IP
    data_server_ip = get_input_value(
        defaults.DATA_SERVER_IP,
        cliargs["data_server_ip"],
        configargs.get("data_server_ip"),
    )
    data_server_port = get_input_value(
        defaults.DATA_SERVER_PORT,
        cliargs["data_server_port"],
        configargs.get("data_server_port"),
    )

    # Create test config object
    config = ts.TestConfig(
        test_name=cliargs["test_name"],
        data_server_ip=data_server_ip,
        data_server_port=data_server_port,
        chunk_size=int(
            get_input_value(
                defaults.CHUNK_SIZE, cliargs["chunk_size"], configargs.get("chunk_size")
            )
        ),
        chunks=int(
            get_input_value(
                defaults.CHUNKS, cliargs["chunks"], configargs.get("chunks")
            )
        ),
        sut_brand=get_input_value(
            defaults.SUT, cliargs["sut_brand"], configargs.get("sut_brand")
        ),
        sut_hardware=get_input_value(
            defaults.SUT, cliargs["sut_hardware"], configargs.get("sut_hardware")
        ),
        sut_software=get_input_value(
            defaults.SUT, cliargs["sut_software"], configargs.get("sut_software")
        ),
        data_server_listen_port=int(
            get_input_value(
                defaults.DATA_SERVER_LISTEN_PORT,
                cliargs["data_server_listen_port"],
                configargs.get("data_server_listen_port"),
            )
        ),
        ssid=get_input_value(cliargs["ssid"], defaults.SSID, configargs.get("ssid")),
        generate_pcap=get_input_value(
            defaults.GENERATE_PCAP,
            not cliargs["no_pcap"],
            configargs.get("generate_pcap"),
        ),
        generate_report=get_input_value(
            defaults.GENERATE_REPORT,
            not cliargs["no_test"],
            configargs.get("generate_report"),
        ),
        upload_chunks=get_input_value(
            defaults.UPLOAD_CHUNKS,
            not cliargs["no_upload"],
            configargs.get("upload_chunks"),
        ),
        download_chunks=get_input_value(
            defaults.DOWNLOAD_CHUNKS,
            not cliargs["no_download"],
            configargs.get("download_chunks"),
        ),
        markers=get_input_value(
            possible_markers, cliargs["markers"], configargs.get("markers")
        ),
        client_interface=get_input_value(
            defaults.WIRELESS_IFACE,
            cliargs["client_interface"],
            configargs.get("client_interface"),
        ),
        server_interface=get_input_value(
            defaults.WIRED_IFACE,
            cliargs["server_interface"],
            configargs.get("server_interface"),
        ),
        local_output_directory=get_input_value(
            defaults.ROOT_DIR,
            cliargs["local_output_directory"],
            configargs.get("local_output_directory"),
        ),
    )
    return config


def main():
    # Parse command line arguments and set up logging.
    cliargs_orig = parse_cliargs()
    cliargs = vars(cliargs_orig)
    logger = logging.getLogger(__name__)
    ts.setup_logging(cliargs_orig.debug)

    # Create TestConfig object
    if not cliargs["config"]:
        configargs = {}
    else:
        config_file = cliargs["config"]
        with open(config_file, "r") as file:
            configargs = yaml.safe_load(file)
    config = get_testconfig(cliargs, configargs)

    # Create directories
    logger.info(f"Creating subdirectories in {config.local_output_directory}")
    files.init_dirs(config.local_output_directory)
    config.write_yaml()

    # Generate PCAP if enabled.
    if config.generate_pcap:
        ts.generate_pcap(config, logger)

    # Execute tests if enabled.
    if config.generate_report:
        execute_test_cases(config, logger)


if __name__ == "__main__":
    main()
