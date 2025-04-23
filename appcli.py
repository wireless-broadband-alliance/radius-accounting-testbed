"""CLI for RADIUS Accounting Assurance Test Bed"""

import argparse
import src.testbed_setup as ts
import logging
import pytest
import yaml
import os
from src.metadata import get_metadata
import src.inputs as inputs
from typing import Union
import src.files as files


def get_possible_markers():
    """Generate markers from pytest.ini file."""
    curdir = os.path.dirname(os.path.abspath(__file__))
    pytest_ini_file = os.path.join(curdir, inputs.RELATIVE_PYTEST_INI)
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
        help="IP of the data server for uploading and downloading",
    )
    parser.add_argument(
        "data_server_port",
        type=int,
        default=None,
        help="Port of the data server for uploading and downloading",
    )
    parser.add_argument(
        "--config", type=str, help="Optional config file to get input from"
    )
    parser.add_argument(
        f"--{inputs.KEY_MARKERS}",
        type=str,
        default=None,
        help=f"Test Markers: {markers_str}",
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        f"--{inputs.KEY_DATA_SERVER_LISTEN_PORT}",
        type=int,
        default=None,
        help=f"default: {inputs.DATA_SERVER_LISTEN_PORT}",
    )
    parser.add_argument(
        f"--{inputs.KEY_ROOT_DIR}",
        type=str,
        default=None,
        help=f"default: {inputs.ROOT_DIR}",
    )
    parser.add_argument(
        f"--{inputs.KEY_CHUNK_SIZE}",
        type=int,
        default=None,
        help=f"default: {inputs.CHUNK_SIZE}",
    )
    parser.add_argument(
        f"--{inputs.KEY_CHUNKS}",
        type=int,
        default=None,
        help=f"Number of chunks to pull, default: {inputs.CHUNKS}",
    )
    parser.add_argument(
        f"--{inputs.KEY_SSID}", type=str, default=None, help=f"default: {inputs.SSID}"
    )
    parser.add_argument(
        f"--{inputs.KEY_SOFTWARE}",
        type=str,
        default=None,
        help="Software info for System Under Test (SUT)",
    )
    parser.add_argument(
        f"--{inputs.KEY_BRAND}",
        type=str,
        default=None,
        help="Brand of System Under Test (SUT)"
    )
    parser.add_argument(
        f"--{inputs.KEY_HARDWARE}",
        type=str,
        default=None,
        help="Hardware info for System Under Test (SUT)",
    )
    parser.add_argument(
        f"--{inputs.KEY_CLIENT_IFACE}",
        type=str,
        default=None,
        help=f"default: {inputs.CLIENT_IFACE}",
    )
    parser.add_argument(
        f"--{inputs.KEY_SERVER_IFACE}",
        type=str,
        default=None,
        help=f"default: {inputs.SERVER_IFACE}",
    )
    parser.add_argument(
        f"--{inputs.KEY_RADIUS_PORT}",
        type=int,
        help=f"RADIUS server auth port, default: {inputs.RADIUS_PORT}",
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

def convert_markers(markers: str) -> list:
    """Convert markers string to list."""
    possible_delims = [",", ";", " "]
    #convert to list if delim is found
    for delim in possible_delims:
        if delim in markers:
            break
    markers_tmp = markers.split(delim)
    spaces_removed = [marker.strip() for marker in markers_tmp]
    #Get rid of empty strings
    return [marker for marker in spaces_removed if marker]

def execute_test_cases(config: ts.TestConfig, logger: logging.Logger):
    """Run tests against PCAP."""
    test_name = config.test_name
    metadata = get_metadata(test_name, config.local_output_directory)
    logger.info(f'\n\nMetadata for "{test_name}":\n{metadata.pretty_print_format()}\n')
    markers = " or ".join(config.markers)
    pytest_args = ["-v", "raatests", "--test_name", test_name]
    extra_args = ["-m", markers]
    logger.debug(f"\n\npytest args: {pytest_args + extra_args}\n")
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

def import_config_file(cliargs: dict) -> dict:
    """Import config file and return as dict."""
    if not cliargs["config"]:
        configargs = {}
    else:
        config_file = cliargs["config"]
        with open(config_file, "r") as file:
            configargs = yaml.safe_load(file)
    return configargs

def create_testconfig(args_from_cli, args_from_config):
    """Create TestConfig object"""
    test_name = args_from_cli["test_name"]
    data_server_ip = args_from_cli["data_server_ip"]
    data_server_port = args_from_cli["data_server_port"]
    return ts.get_testconfig(test_name, data_server_ip, data_server_port, args_from_cli, args_from_config)

def main():
    #Parse CLI and config file args
    cliargs = vars(parse_cliargs())
    cliargs[inputs.KEY_DOWNLOAD_CHUNKS] = not cliargs.pop('no_download')
    cliargs[inputs.KEY_UPLOAD_CHUNKS] = not cliargs.pop('no_upload')
    cliargs["markers"] = change_marker_format(cliargs["markers"])
    configargs = import_config_file(cliargs)

    #Set up logging
    logger = logging.getLogger(__name__)
    ts.setup_logging(cliargs["debug"])

    #Create TestConfig object from CLI + config args
    config = create_testconfig(cliargs, configargs)

    # Create directories
    logger.info(f"Creating subdirectories in {config.local_output_directory}")
    files.init_dirs(config.local_output_directory)
    config.write_yaml()

    # Generate PCAP if enabled.
    if config.generate_pcap:
        ts.generate_pcap(config, logger, cliargs["debug"])

    # Execute tests if enabled.
    if config.generate_report:
        execute_test_cases(config, logger)


if __name__ == "__main__":
    main()
