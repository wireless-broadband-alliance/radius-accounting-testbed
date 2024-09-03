"""CLI for RADIUS Accounting Assurance Test Bed"""

import argparse
import raatestbed.test_setup as ts
import logging
import pytest
import yaml
import sys
from raatestbed.metadata import get_metadata
import raatestbed.defaults as defaults
from raatestbed.files import init_dirs

# TODO: dynamically generate tags/markers from pytest
TEST_TAGS = ["core", "core_upload", "core_download", "openroaming"]


def parse_cliargs():
    parser = argparse.ArgumentParser()
    parser.add_argument("test_name", type=str, help="Name of the test to run")
    parser.add_argument(
        "--download_data_server_ip",
        type=str,
        default=None,
        help="IP of the server to download data from",
    )
    parser.add_argument(
        "--download_data_server_port",
        type=int,
        default=None,
        help="Port of the server to download data from",
    )
    parser.add_argument(
        "--upload_data_server_ip",
        type=str,
        default=None,
        help="IP of the server to upload data to",
    )
    parser.add_argument(
        "--upload_data_server_port",
        type=int,
        default=None,
        help="Port of the server to upload data to",
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
    parser.add_argument("--no_upload", action="store_true", help="No not upload chunks")
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
    if user_wants_to_continue(f'Run test suites "{markers_log}"'):
        pytest.main(pytest_args + extra_args)


def get_input_value(cliarg, default_value, configarg):
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


def get_testconfig(cliargs, configargs) -> ts.TestConfig:
    """Create TestConfig object with CLI args WITH config file."""
    cliargs["markers"] = change_marker_format(cliargs["markers"])
    config = ts.TestConfig(
        test_name=cliargs["test_name"],
        upload_data_server_ip=get_input_value(
            cliargs["upload_data_server_ip"],
            defaults.UPLOAD_DATA_SERVER_IP,
            configargs.get("upload_data_server_ip"),
        ),
        upload_data_server_port=get_input_value(
            cliargs["upload_data_server_port"],
            defaults.UPLOAD_DATA_SERVER_PORT,
            configargs.get("upload_data_server_port"),
        ),
        download_data_server_ip=get_input_value(
            cliargs["download_data_server_ip"],
            defaults.DOWNLOAD_DATA_SERVER_IP,
            configargs.get("download_data_server_ip"),
        ),
        download_data_server_port=get_input_value(
            cliargs["download_data_server_port"],
            defaults.DOWNLOAD_DATA_SERVER_PORT,
            configargs.get("download_data_server"),
        ),
        chunk_size=int(
            get_input_value(
                cliargs["chunk_size"], defaults.CHUNK_SIZE, configargs.get("chunk_size")
            )
        ),
        chunks=int(
            get_input_value(
                cliargs["chunks"], defaults.CHUNK_SIZE, configargs.get("chunks")
            )
        ),
        sut_brand=get_input_value(
            cliargs["sut_brand"], defaults.SUT, configargs.get("sut_brand")
        ),
        sut_hardware=get_input_value(
            cliargs["sut_hardware"], defaults.SUT, configargs.get("sut_hardware")
        ),
        sut_software=get_input_value(
            cliargs["sut_software"], defaults.SUT, configargs.get("sut_software")
        ),
        data_server_listen_port=int(
            get_input_value(
                cliargs["data_server_listen_port"],
                defaults.DATA_SERVER_LISTEN_PORT,
                configargs.get("data_server_listen_port"),
            )
        ),
        ssid=get_input_value(cliargs["ssid"], defaults.SSID, configargs.get("ssid")),
        generate_pcap=get_input_value(
            not cliargs["no_pcap"],
            defaults.GENERATE_PCAP,
            configargs.get("generate_pcap"),
        ),
        generate_report=get_input_value(
            not cliargs["no_test"],
            defaults.GENERATE_REPORT,
            configargs.get("generate_report"),
        ),
        upload_chunks=get_input_value(
            not cliargs["no_upload"],
            defaults.UPLOAD_CHUNKS,
            configargs.get("upload_chunks"),
        ),
        download_chunks=get_input_value(
            not cliargs["no_download"],
            defaults.DOWNLOAD_CHUNKS,
            configargs.get("download_chunks"),
        ),
        markers=get_input_value(
            cliargs["markers"], configargs.get("markers"), TEST_TAGS
        ),
        client_interface=get_input_value(
            cliargs["client_interface"],
            defaults.WIRELESS_IFACE,
            configargs.get("client_interface"),
        ),
        server_interface=get_input_value(
            cliargs["server_interface"],
            defaults.WIRED_IFACE,
            configargs.get("server_interface"),
        ),
        local_output_directory=get_input_value(
            cliargs["local_output_directory"],
            defaults.ROOT_DIR,
            configargs.get("local_output_directory"),
        ),
    )
    return config


# def get_testconfig_without_config_file(cliargs) -> ts.TestConfig:
#    """Create TestConfig object with CLI args WITHOUT config file."""
#    cliargs["markers"] = change_marker_format(cliargs["markers"])
#    config = ts.TestConfig(
#        test_name=cliargs["test_name"],
#        upload_data_server_ip=cliargs["upload_data_server_ip"],
#        upload_data_server_port=cliargs["upload_data_server_port"],
#        download_data_server_ip=cliargs["download_data_server_ip"],
#        download_data_server_port=cliargs["download_data_server_port"],
#        chunk_size=int(get_input_value(cliargs["chunk_size"], defaults.CHUNK_SIZE)),
#        chunks=int(get_input_value(cliargs["chunks"], defaults.CHUNKS)),
#        data_server_listen_port=int(
#            get_input_value(
#                cliargs["data_server_listen_port"], defaults.DATA_SERVER_LISTEN_PORT
#            )
#        ),
#        ssid=get_input_value(cliargs["ssid"], defaults.SSID),
#        generate_pcap=get_input_value(not cliargs["no_pcap"], defaults.GENERATE_PCAP),
#        generate_report=get_input_value(
#            not cliargs["no_test"], defaults.GENERATE_REPORT
#        ),
#        upload_chunks=get_input_value(not cliargs["no_upload"], defaults.UPLOAD_CHUNKS),
#        download_chunks=get_input_value(
#            not cliargs["no_download"], defaults.DOWNLOAD_CHUNKS
#        ),
#        markers=get_input_value(cliargs["markers"], TEST_TAGS),
#        client_interface=get_input_value(
#            cliargs["client_interface"], defaults.WIRELESS_IFACE
#        ),
#        server_interface=get_input_value(
#            cliargs["server_interface"], defaults.WIRED_IFACE
#        ),
#        local_output_directory=get_input_value(
#            cliargs["local_output_directory"], defaults.ROOT_DIR
#        ),
#        sut_brand=get_input_value(cliargs["sut_brand"], defaults.SUT),
#        sut_hardware=get_input_value(cliargs["sut_hardware"], defaults.SUT),
#        sut_software=get_input_value(cliargs["sut_software"], defaults.SUT),
#    )
#    return config


def main():
    # Parse command line arguments and set up logging.
    cliargs_orig = parse_cliargs()
    cliargs = vars(cliargs_orig)
    logger = logging.getLogger(__name__)
    ts.setup_logging(cliargs_orig.debug)

    # Check that either upload or download data server IP is provided.
    if not cliargs["upload_data_server_ip"] and not cliargs["download_data_server_ip"]:
        logger.error("Either upload or download data server IP must be provided.")
        sys.exit(1)

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
    init_dirs(config.local_output_directory)
    config.write_yaml()

    # Generate PCAP if enabled.
    if config.generate_pcap:
        ts.generate_pcap(config, logger)

    # Execute tests if enabled.
    if config.generate_report:
        execute_test_cases(config, logger)


if __name__ == "__main__":
    main()
