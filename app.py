import streamlit as st
import logging
import raatestbed.test_setup as ts
import pytest
import time
import yaml
from typing import List
from streamlit.logger import get_logger
from raatestbed.test_setup import TestConfig

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


def get_selected_markers(possible_markers, checked_markers=[]) -> List[str]:
    """Returns a dictionary of selected pytest markers"""
    # Checkbox for selecting tests
    st.header("Test Marker/Tag Selection")
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
    """Data Server IP input field"""
    help = "This is the IP of the data server used for uploading or downloading chunks of data."
    if isinstance(value, str):
        return st.text_input("Data Server IP", value=value, help=help)
    return st.text_input("Data Server IP", help=help)


def text_input_data_server_port(value="") -> str:
    """Data Server port input field"""
    help = "This is the port of the data server used for uploading or downloading chunks of data."
    if value:
        return st.text_input("Data Server Port", value=value, help=help)
    return st.text_input("Data Server Port", help=help)


def number_input_chunk_size(value=DEFAULT_CHUNK_SIZE):
    """Chunk Size input field"""
    help = "Size of the data chunks to be uploaded or downloaded."
    return int(
        st.number_input("Chunk Size", value=value, min_value=1, step=1, help=help)
    )


def number_input_num_chunks(value=DEFAULT_CHUNKS):
    """Number of Chunks input field"""
    help = "Number of data chunks to be uploaded or downloaded."
    return int(
        st.number_input("Number of Chunks", value=value, min_value=1, step=1, help=help)
    )


def text_input_data_server_listen_port(value=DEFAULT_DATA_SERVER_LISTEN_PORT) -> str:
    """Data Server Listen Port input field"""
    help = "Local port on the test bed to listen for data server connections. NOTE: This should be different from the data server port above. Your system under test network needs to forward ports from data_server_ip:data_server_port to this port."
    return st.text_input("Data server listen port", value=str(value), help=help)


def text_input_ssid(value=DEFAULT_SSID):
    """SSID input field"""
    help = "SSID of the wireless network that the client will connect to."
    return st.text_input("Wireless Network Name (SSID)", value=value, help=help)


def text_input_sut_make(value=DEFAULT_SUT):
    """Brand of System Under Test (SUT)"""
    help = "Brand of System Under Test (SUT)"
    return st.text_input("SUT Make", value=value, help=help)


def text_input_sut_model(value=DEFAULT_SUT):
    """Model of System Under Test (SUT)"""
    help = "Model of System Under Test (SUT)"
    return st.text_input("SUT Model", value=value, help=help)


def text_input_sut_firmware(value=DEFAULT_SUT):
    """Firmware version of System Under Test (SUT)"""
    help = "Firmware version of System Under Test (SUT)"
    return st.text_input("SUT Firmware Version", value=value, help=help)


def checkbox_select_test_parts(
    value_generate_pcap=DEFAULT_GENERATE_PCAP,
    value_generate_report=DEFAULT_GENERATE_REPORT,
):
    """Checkbox to select which parts of the test to run"""
    generate_pcap = st.checkbox("Generate PCAP", value=value_generate_pcap)
    execute_test_cases = st.checkbox("Execute Test Cases", value=value_generate_report)
    return generate_pcap, execute_test_cases


def text_input_client_interface(default=DEFAULT_WIRELESS_IFACE):
    """Wireless interface input field"""
    help = "Wireless interface used by the 802.1X client."
    return st.text_input("Wireless Client Interface", value=default, help=help)


def text_input_server_interface(default=DEFAULT_WIRED_IFACE):
    """Wired interface input field"""
    help = "Wired interface used by the RADIUS and data servers."
    return st.text_input("Wired Server Interface", value=default, help=help)


def text_input_local_output_directory(default=DEFAULT_ROOT_DIR):
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


st.title("RADIUS Accounting Assurance Test Bed")
uploaded_file = st.file_uploader("Upload config file", type=["yaml"])

# Main form showing all inputs
with st.form(key="main"):
    st.header("Test Configuration")

    # If user uploaded config file, then present those values from the config
    if uploaded_file is not None:
        data = yaml.safe_load(uploaded_file)
        test_name = text_input_test_name(data["test_name"])
        data_server_ip = text_input_data_server_ip(data["data_server_ip"])
        data_server_port = text_input_data_server_port(data["data_server_port"])
        chunk_size = number_input_chunk_size(data["chunk_size"])
        chunks = number_input_num_chunks(data["chunks"])
        data_server_listen_port = text_input_data_server_listen_port(
            data["data_server_listen_port"]
        )
        ssid = text_input_ssid(data["ssid"])
        sut_make = text_input_sut_make(data["sut_make"])
        sut_model = text_input_sut_model(data["sut_model"])
        sut_firmware = text_input_sut_firmware(data["sut_firmware"])
        checkbox_generate_pcap, checkbox_execute_test_cases = (
            checkbox_select_test_parts(data["generate_pcap"], data["generate_report"])
        )
        markers = get_selected_markers(TEST_TAGS, data["markers"])
        client_interface = text_input_client_interface(data["client_interface"])
        server_interface = text_input_server_interface(data["server_interface"])
        local_output_directory = text_input_local_output_directory(
            data["local_output_directory"]
        )

    else:
        test_name = text_input_test_name()
        data_server_ip = text_input_data_server_ip()
        data_server_port = text_input_data_server_port()
        chunk_size = number_input_chunk_size()
        chunks = number_input_num_chunks()
        data_server_listen_port = text_input_data_server_listen_port()
        ssid = text_input_ssid()
        sut_make = text_input_sut_make()
        sut_model = text_input_sut_model()
        sut_firmware = text_input_sut_firmware()
        # PCAP generation + report selection
        checkbox_generate_pcap, checkbox_execute_test_cases = (
            checkbox_select_test_parts()
        )
        # Marker Selection
        markers = get_selected_markers(TEST_TAGS)

        # Advanced Settings
        st.subheader("Advanced Settings")
        client_interface = text_input_client_interface()
        server_interface = text_input_server_interface()
        local_output_directory = text_input_local_output_directory()

    update_widget("")
    # Button to start the tests
    if st.form_submit_button("Run Tests"):
        # Create the test configuration
        config = TestConfig(
            test_name=test_name,
            data_server_ip=data_server_ip,
            data_server_port=int(data_server_port),
            chunk_size=chunk_size,
            chunks=chunks,
            data_server_listen_port=int(data_server_listen_port),
            ssid=ssid,
            sut_make=sut_make,
            sut_model=sut_model,
            sut_firmware=sut_firmware,
            generate_pcap=checkbox_generate_pcap,
            generate_report=checkbox_execute_test_cases,
            markers=markers,
            client_interface=client_interface,
            server_interface=server_interface,
            local_output_directory=local_output_directory,
        )
        config.write_yaml()

        logger = get_logger(__name__)
        handler = StreamlitLogHandler(st.empty().code)
        logger.addHandler(handler)
        if checkbox_generate_pcap:
            ts.generate_pcap(config, logger)
        if checkbox_execute_test_cases:
            execute_test_cases(config, logger, markers)
