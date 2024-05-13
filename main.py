import time
import os
import logging
import argparse
import psutil

import processes as procs
from data_transfer import TCPServer, get_data_chunk

# TODO: Add user interface to setup and control test


# check if network interface has IP
def check_for_ip(interface):
    addrs = psutil.net_if_addrs()
    if interface not in addrs:
        return False
    if not addrs[interface]:
        return False
    return True


# parse arguments and look for --debug flag
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--logs_dir", type=str, default="logs")
    parser.add_argument("--pcap_dir", type=str, default="pcap")
    return parser.parse_args()


def setup_logging(debug):
    if debug:
        logging.basicConfig(
            level=logging.DEBUG, format="%(asctime)s - %(levelname)s: %(message)s"
        )
    else:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


def create_dir_if_not_exists(directory):
    if not os.path.exists(directory):
        logging.info(f"Creating directory {directory}")
        os.makedirs(directory)


def main():
    args = parse_args()
    setup_logging(args.debug)

    # TODO: Add user interface to select these values
    ssid = "raatest2"
    wireless_interface = "wlan0"
    wired_interface = "eth0"
    data_server_ip = "192.168.124.1"
    data_server_port = 8000
    data_chunk_size = 1024**2

    # Initialize log file and pcap locations
    create_dir_if_not_exists(args.logs_dir)
    create_dir_if_not_exists(args.pcap_dir)
    radius_tcpdump_log = os.path.join(args.logs_dir, "tcpdump.radius.log")
    freeradius_log = os.path.join(args.logs_dir, "freeradius.log")
    wpa_supplicant_log = os.path.join(args.logs_dir, "wpa_supplicant.log")
    radius_pcap_location = os.path.join(args.pcap_dir, "tcpdump.radius.pcap")

    # Initialize objects
    radius_tcpdump = procs.TCPDump(
        interface=wired_interface,
        pcap_location=radius_pcap_location,
        log_location=radius_tcpdump_log,
    )
    freeradius = procs.FreeRADIUS(log_location=freeradius_log, debug=args.debug)
    wpasupplicant = procs.WpaSupplicant(
        interface=wireless_interface, log_location=wpa_supplicant_log, ssid=ssid
    )
    data_server = TCPServer(8000, 1024**2)

    # Start demo
    logging.info("Starting RADIUS tcpdump")
    radius_tcpdump.start()
    logging.info("Starting FreeRADIUS")
    freeradius.start()
    logging.info("Starting wpa_supplicant")
    wpasupplicant.start()
    logging.info("Starting data server")
    data_server.start()

    logging.info(f"Waiting for IP on {wireless_interface}...")
    while not check_for_ip(wireless_interface):
        pass

    time.sleep(3)
    logging.info(f"Downloading data from {data_server_ip}:{data_server_port}...")
    get_data_chunk(
        server_host=data_server_ip,
        server_port=data_server_port,
        chunk_size=data_chunk_size,
        iface=wireless_interface,
    )
    time.sleep(5)
    freeradius.stop()
    data_server.stop()
    wpasupplicant.stop()
    radius_tcpdump.stop()
    logging.info("Demo complete")


if __name__ == "__main__":
    main()
