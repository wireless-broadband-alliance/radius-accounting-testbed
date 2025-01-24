"""Streamlit UI for RADIUS Accounting Assurance Test Bed"""

import streamlit as st
import logging
import src.testbed_setup as ts
import pytest
import time
import yaml
import os
from typing import List
from streamlit.logger import get_logger
from src.testbed_setup import TestConfig
import src.files as files
import src.inputs as inputs


def get_selected_markers(possible_markers, checked_markers=[]) -> List[str]:
    """Returns a dictionary of selected pytest markers"""
    # Checkbox for selecting tests
    st.header("Test Marker/Tag")
    results = dict()
    for marker in possible_markers:
        if marker in checked_markers:
            results[marker] = st.checkbox(marker, value=True)
        else:
            results[marker] = st.checkbox(marker)
    return [marker for marker, selected in results.items() if selected]

def text_input_test_name(value=None):
    """Test Name input field"""
    help = "This is the name of the test that will be run. It will be used to identify the test and produce output files with this name."
    if isinstance(value, str):
        return st.text_input("Test Name", value=value, help=help)
    return st.text_input("Test Name", help=help)


def text_input_data_server_ip(value=None):
    """Data Server IP input field for download"""
    help = "This is the IP of the data server used for downloading and uploading chunks of data."
    text = "Data Server IP"
    if isinstance(value, str):
        return st.text_input(text, value=value, help=help)
    return st.text_input(text, help=help)


def text_input_data_server_port(value="") -> str:
    """Data Server port input field for download"""
    help = "This is the port of the data server used for downloading and uploading chunks of data."
    text = "Data Server Port"
    if value:
        return st.text_input(text, value=value, help=help)
    return st.text_input(text, help=help)


def number_input_chunk_size(value=inputs.CHUNK_SIZE):
    """Chunk Size input field"""
    help = "Size of the data chunks to be uploaded or downloaded."
    return int(
        st.number_input("Chunk Size", value=value, min_value=1, step=1, help=help)
    )


def number_input_num_chunks(value=inputs.CHUNKS):
    """Number of Chunks input field"""
    help = "Number of data chunks to be uploaded or downloaded."
    return int(
        st.number_input("Number of Chunks", value=value, min_value=1, step=1, help=help)
    )


def text_input_data_server_listen_port(value=inputs.DATA_SERVER_LISTEN_PORT) -> str:
    """Data Server Listen Port input field"""
    help = "Local port on the test bed to listen for data server connections. NOTE: This should be different from the data server port above. Your system under test network needs to forward ports from data_server_ip:data_server_port to this port."
    return st.text_input("Data server listen port", value=str(value), help=help)


def text_input_ssid(value=inputs.SSID):
    """SSID input field"""
    help = "SSID of the wireless network that the client will connect to."
    return st.text_input("Wireless Network Name (SSID)", value=value, help=help)


def text_input_sut_brand(value=inputs.BRAND):
    """Brand of System Under Test (SUT)"""
    help = "Brand of System Under Test (SUT)"
    return st.text_input("SUT Model", value=value, help=help)


def text_input_sut_hardware(value=inputs.HARDWARE):
    """hardware of System Under Test (SUT)"""
    help = "Hardware info for System Under Test (SUT)"
    return st.text_input("SUT Hardware", value=value, help=help)


def text_input_sut_software(value=inputs.SOFTWARE):
    """software version of System Under Test (SUT)"""
    help = "Software info for System Under Test (SUT)"
    return st.text_input("SUT Software", value=value, help=help)


def checkbox_select_upload_download(
    value_upload=inputs.UPLOAD_CHUNKS,
    value_download=inputs.DOWNLOAD_CHUNKS,
):
    """Checkbox to select to upload and/or download chunks"""
    st.header("Upload/Download")
    upload_chunks = st.checkbox("Upload Chunks", value=value_upload)
    download_chunks = st.checkbox("Download Chunks", value=value_download)
    return upload_chunks, download_chunks


def checkbox_select_test_parts(
    value_generate_pcap=inputs.GENERATE_PCAP,
    value_generate_report=inputs.GENERATE_REPORT,
):
    """Checkbox to select which parts of the test to run"""
    st.header("Test Part")
    generate_pcap = st.checkbox("Generate PCAP", value=value_generate_pcap)
    execute_test_cases = st.checkbox("Execute Test Cases", value=value_generate_report)
    return generate_pcap, execute_test_cases


def text_input_client_interface(default=inputs.CLIENT_IFACE):
    """Client interface input field"""
    help = "Wireless interface used by the 802.1X client."
    return st.text_input("Client Interface", value=default, help=help)


def text_input_server_interface(default=inputs.SERVER_IFACE):
    """Server interface input field"""
    help = "Interface used by the RADIUS and data servers."
    return st.text_input("Server Interface", value=default, help=help)


def text_input_local_output_directory(default=inputs.ROOT_DIR):
    help = (
        "Local output directory on the test bed where the test results will be stored."
    )
    return st.text_input("Output directory on test bed", value=default, help=help)


class StreamlitLogHandler(logging.Handler):
    def __init__(self, widget_update_func):
        super().__init__()
        self.widget_update_func = widget_update_func

    def emit(self, record):
        msg = self.format(record)
        self.widget_update_func(msg)


def update_widget(msg):
    st.write(msg)

def get_possible_markers():
    """Generate markers from pytest.ini file."""
    curdir = os.path.dirname(os.path.abspath(__file__))
    pytest_ini_file = os.path.join(curdir, inputs.RELATIVE_PYTEST_INI)
    return files.get_marker_list(pytest_ini_file)

def execute_test_cases(
    config: ts.TestConfig, logger: logging.Logger, markers: List[str]
):
    """Run tests against PCAP."""
    test_name = config.test_name
    markers_str = " or ".join(markers)
    logger.info("Executing Test Cases")
    pytest_args = ["-v", "raatests", "--test_name", test_name]
    extra_args = ["-m", markers_str]
    pytest.main(pytest_args + extra_args)
    logger.info(f"Finished test cases for {test_name} with markers: {markers_str}")
    time.sleep(2)
    logger.info(f"Tests executed. Results written to {config.local_output_directory}")

def get_all_optional_inputs(uploaded_file):
    """Merge default values with user input"""
    if uploaded_file is not None:
        data_config = yaml.safe_load(uploaded_file)
        all_inputs = inputs.get_all_args(data_config)
    else:
        all_inputs = inputs.get_all_args()
    return all_inputs

def build_form(opts):
    """Build the form with given options"""
    # NOTE: Form will be built in order of the inputs
    test_name = text_input_test_name()
    chunk_size = number_input_chunk_size(opts[inputs.KEY_CHUNK_SIZE])
    chunks = number_input_num_chunks(opts[inputs.KEY_CHUNKS])
    data_server_listen_port = text_input_data_server_listen_port(
        opts[inputs.KEY_DATA_SERVER_LISTEN_PORT]
    )
    ssid = text_input_ssid(opts[inputs.KEY_SSID])
    sut_brand = text_input_sut_brand(opts[inputs.KEY_BRAND])
    sut_hardware = text_input_sut_hardware(opts[inputs.KEY_HARDWARE])
    sut_software = text_input_sut_software(opts[inputs.KEY_SOFTWARE])
    checkbox_upload_chunks, checkbox_download_chunks = checkbox_select_upload_download(
        opts[inputs.KEY_UPLOAD_CHUNKS], opts[inputs.KEY_DOWNLOAD_CHUNKS]
    )
    if checkbox_upload_chunks or checkbox_download_chunks:
        data_server_ip = text_input_data_server_ip()
        data_server_port = text_input_data_server_port()
        checkbox_generate_pcap, checkbox_execute_test_cases = checkbox_select_test_parts(
            opts[inputs.KEY_GENERATE_PCAP], opts[inputs.KEY_GENERATE_REPORT]
    )
    possible_markers = get_possible_markers()
    markers = get_selected_markers(possible_markers, opts[inputs.KEY_MARKERS])
    client_interface = text_input_client_interface(opts[inputs.KEY_CLIENT_IFACE])
    server_interface = text_input_server_interface(opts[inputs.KEY_SERVER_IFACE])
    local_output_directory = text_input_local_output_directory(
        opts[inputs.KEY_ROOT_DIR]
    )
    # Create TestConfig object with all the inputs
    config = TestConfig(
        test_name=test_name,
        data_server_ip=data_server_ip,
        data_server_port=data_server_port,
        chunk_size=chunk_size,
        chunks=chunks,
        data_server_listen_port=data_server_listen_port,
        ssid=ssid,
        sut_brand=sut_brand,
        sut_hardware=sut_hardware,
        sut_software=sut_software,
        generate_pcap=checkbox_generate_pcap,
        generate_report=checkbox_execute_test_cases,
        upload_chunks=checkbox_upload_chunks,
        download_chunks=checkbox_download_chunks,
        markers=markers,
        client_interface=client_interface,
        server_interface=server_interface,
        local_output_directory=local_output_directory,
    )
    return config

def main():

    # Set up logger
    logger = get_logger(__name__)

    # Set header and see if a file is uploaded
    st.title("RADIUS Accounting Assurance Test Bed")
    uploaded_file = st.file_uploader("Upload config file", type=["yaml"])
    st.header("Test Configuration")

    # Get all optional inputs, populate form with either default or uploaded values
    optional_inputs = get_all_optional_inputs(uploaded_file)
    config = build_form(optional_inputs)
    update_widget("")

    # Run Tests when button is clicked
    if st.button("Run Tests"):
        config.write_yaml()
        handler = StreamlitLogHandler(st.empty().code)
        logger.addHandler(handler)
        if config.generate_pcap:
            ts.generate_pcap(config, logger)
        if config.execute_test_cases:
            execute_test_cases(config, logger, config.markers)


if __name__ == "__main__":
    main()
