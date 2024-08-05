import argparse
import raatestbed.test_setup as ts

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



def main():
    # Parse command line arguments and set up logging.
    cliargs_orig = parse_cliargs()
    cliargs = vars(cliargs_orig)
    ts.setup_logging(cliargs_orig.debug)
    markers = cliargs["markers"].split(",")
    config = ts.TestConfig(
        test_name=cliargs["test_name"],
        data_server_ip=cliargs["data_server_ip"],
        data_server_port=cliargs["data_server_port"],
        chunk_size=cliargs["chunk_size"],
        chunks=cliargs["chunks"],
        data_server_listen_port=cliargs["data_server_listen_port"],
        ssid=cliargs["ssid"],
        generate_pcap=not cliargs["no_pcap"],
        generate_report=not cliargs["no_test"],
        markers=markers,
        client_interface = cliargs["wireless_interface"],
        server_interface = cliargs["wired_interface"],
        local_output_directory=cliargs["root_dir"],
    )

    # Generate PCAP.
    if not cliargs["no_pcap"]:
        ts.generate_pcap(config)

    # Execute tests.
    if not cliargs["no_test"]:
        ts.execute_test_cases(config)


if __name__ == "__main__":
    main()
