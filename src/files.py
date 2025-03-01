"""Contains filenames and directories used in the project."""

import os
import configparser


SUBDIRS = {
    "metadata": "metadata",
    "pcap": "pcap",
    "reports": "reports",
    "config": "config",
    "logs": "logs",
}

def init_dirs(root_dir: str):
    """Initialize all directory."""
    os.makedirs(root_dir, exist_ok=True)
    init_subdirectories(root_dir)


def get_marker_list(ini_file="pytest.ini") -> list:
    """Return list of markers from pytest ini file."""
    config = configparser.ConfigParser()
    config.read(ini_file)
    test_markers = config["pytest"]["markers"].split("\n")[1:]
    test_markers = [marker.split(":")[0] for marker in test_markers]
    return test_markers


def init_subdirectories(root_dir: str):
    """Initialize directories."""
    for dir_name in [
        get_pcap_dir,
        get_metadata_dir,
        get_reports_dir,
        get_config_dir,
        get_logs_dir,
    ]:
        os.makedirs(dir_name(root_dir), exist_ok=True)


def get_metadata_dir(root_dir: str) -> str:
    """Return metadata directory."""
    return os.path.join(root_dir, SUBDIRS["metadata"])


def get_pcap_dir(root_dir: str) -> str:
    """Return pcap directory."""
    return os.path.join(root_dir, SUBDIRS["pcap"])


def get_reports_dir(root_dir: str) -> str:
    """Return report directory."""
    return os.path.join(root_dir, SUBDIRS["reports"])


def get_config_dir(root_dir: str) -> str:
    """Return config directory."""
    return os.path.join(root_dir, SUBDIRS["config"])


def get_logs_dir(root_dir: str) -> str:
    """Return logs directory."""
    return os.path.join(root_dir, SUBDIRS["logs"])


def get_metadata_filename(test_name, root_dir) -> str:
    """Return full path of metadata file path for a given test name."""
    metadata_dir = get_metadata_dir(root_dir)
    return os.path.join(metadata_dir, f"{test_name}.metadata.json")


def get_pcap_filename(test_name, root_dir) -> str:
    """Return full path of pcap file path for a given test name."""
    pcap_dir = get_pcap_dir(root_dir)
    return os.path.join(pcap_dir, f"{test_name}.tcpdump.radius.pcap")


def get_report_filename(test_name, root_dir) -> str:
    """Return full path of reports file path for a given test name."""
    report_dir = get_reports_dir(root_dir)
    return os.path.join(report_dir, f"{test_name}.pdf")


def get_config_filename(test_name, root_dir) -> str:
    """Return full path of config file path for a given test name."""
    report_dir = get_config_dir(root_dir)
    return os.path.join(report_dir, f"{test_name}.config.yaml")


def get_freeradius_log_filename(test_name, root_dir) -> str:
    """Return full path of freeradius log file path for a given test name."""
    logs_dir = get_logs_dir(root_dir)
    return os.path.join(logs_dir, f"{test_name}.freeradius.log")


def get_wpasupplicant_log_filename(test_name, root_dir) -> str:
    """Return full path of wpa_supplicant log file path for a given test name."""
    logs_dir = get_logs_dir(root_dir)
    return os.path.join(logs_dir, f"{test_name}.wpasupplicant.log")


def get_tcpdump_log_filename(test_name, root_dir) -> str:
    """Return full path of tcpdump log file path for a given test name."""
    logs_dir = get_logs_dir(root_dir)
    return os.path.join(logs_dir, f"{test_name}.tcpdump.log")


def get_zipped_bundle_filename(test_name, root_dir) -> str:
    """Return full path of config file path for a given test name."""
    return os.path.join(root_dir, f"{test_name}.bundle.zip")


def get_all_files(test_name, root_dir) -> list:
    """Return all files for a given test name."""
    return [
        get_metadata_filename(test_name, root_dir),
        get_pcap_filename(test_name, root_dir),
        get_report_filename(test_name, root_dir),
        get_config_filename(test_name, root_dir),
    ]
