import streamlit as st
import logging
import raatestbed.test_setup as ts
import pytest
import time
from typing import List
from streamlit.logger import get_logger
from raatestbed.test_setup import TestConfig

#TODO: dynamically generate tags/markers from pytest
TEST_TAGS = ['core', 'core-upload', 'openroaming']

from raatestbed.test_setup import DEFAULT_ROOT_DIR
from raatestbed.test_setup import DEFAULT_CHUNK_SIZE
from raatestbed.test_setup import DEFAULT_SSID
from raatestbed.test_setup import DEFAULT_WIRELESS_IFACE
from raatestbed.test_setup import DEFAULT_WIRED_IFACE


def get_selected_markers(possible_markers) -> List[str]:
    """Returns a dictionary of selected pytest markers"""
    # Checkbox for selecting tests
    st.header('Test Marker/Tag Selection')
    results = dict()
    for marker in possible_markers:
        results[marker] = st.checkbox(marker)
    return [marker for marker, selected in results.items() if selected]

def text_input_test_name():
    """Test Name input field"""
    help = "This is the name of the test that will be run. It will be used to identify the test and produce output files with this name."
    return st.text_input('Test Name', help=help)

def text_input_data_server_ip():
    """Data Server IP input field"""
    help = "This is the IP of the data server used for uploading or downloading chunks of data."
    return st.text_input('Data Server IP', help=help)

def text_input_data_server_port():
    """Data Server port input field"""
    help = "This is the port of the data server used for uploading or downloading chunks of data."
    return st.text_input('Data Server Port', help=help)

def number_input_chunk_size():
    """Chunk Size input field"""
    help = "Size of the data chunks to be uploaded or downloaded."
    return int(st.number_input('Chunk Size', value=DEFAULT_CHUNK_SIZE, min_value=1, step=1, help=help))

def number_input_num_chunks():
    """Number of Chunks input field"""
    help = "Number of data chunks to be uploaded or downloaded."
    return int(st.number_input('Number of Chunks', value=1, min_value=1, step=1, help=help))

def text_input_data_server_listen_port():
    """Data Server Listen Port input field"""
    help = "Local port on the test bed to listen for data server connections. NOTE: This should be different from the data server port above. Your system under test network needs to forward ports from data_server_ip:data_server_port to this port."
    return st.text_input('Data server listen port', value="8000", help=help)

def text_input_ssid():
    """SSID input field"""
    help = "SSID of the wireless network that the client will connect to."
    return st.text_input('Wireless Network Name (SSID)', value=DEFAULT_SSID, help=help)

def text_input_sut_make():
    """Brand of System Under Test (SUT)"""
    help = "Brand of System Under Test (SUT)"
    return st.text_input('SUT Make', value="", help=help)

def text_input_sut_model():
    """Model of System Under Test (SUT)"""
    help = "Model of System Under Test (SUT)"
    return st.text_input('SUT Model', value="", help=help)

def text_input_sut_firmware():
    """Firmware version of System Under Test (SUT)"""
    help = "Firmware version of System Under Test (SUT)"
    return st.text_input('SUT Firmware Version', value="", help=help)

def checkbox_select_test_parts():
    """Checkbox to select which parts of the test to run"""
    generate_pcap = st.checkbox("Generate PCAP")
    execute_test_cases = st.checkbox("Execute Test Cases")
    return generate_pcap, execute_test_cases

def text_input_client_interface(default=DEFAULT_WIRELESS_IFACE):
    """Wireless interface input field"""
    help = "Wireless interface used by the 802.1X client."
    return st.text_input('Wireless Client Interface', value=default, help=help)

def text_input_server_interface(default=DEFAULT_WIRED_IFACE):
    """Wired interface input field"""
    help = "Wired interface used by the RADIUS and data servers."
    return st.text_input('Wired Server Interface', value=default, help=help)

def text_input_local_output_directory(default=DEFAULT_ROOT_DIR):
    help = "Local output directory on the test bed where the test results will be stored."
    return st.text_input('Output directory on test bed', value=default, help=help)

class StreamlitLogHandler(logging.Handler):
    def __init__(self, widget_update_func):
        super().__init__()
        self.widget_update_func = widget_update_func

    def emit(self, record):
        msg = self.format(record)
        self.widget_update_func(msg)

def update_widget(msg):
    st.write(msg)

def execute_test_cases(config: ts.TestConfig, logger: logging.Logger, markers: List[str]):
    """Run tests against PCAP."""
    test_name = config.test_name
    markers_str = ",".join(markers)
    logger.info('Executing Test Cases')
    pytest_args = ["-v", "raatests", "--test_name", test_name]
    extra_args = ["-m", markers_str]
    pytest.main(pytest_args + extra_args)
    logger.info(f'Finished test cases for {test_name} with markers: {markers_str}')
    time.sleep(2)
    logger.info(f'Results written to {config.local_output_directory}')

# Main form showing all inputs
with st.form(key='main'):

    st.title('RADIUS Accounting Assurance Test Bed')

    # Main configuration
    st.header('Configuration')
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
    checkbox_generate_pcap, checkbox_execute_test_cases = checkbox_select_test_parts()
    # Marker Selection
    markers = get_selected_markers(TEST_TAGS)

    # Advanced Settings
    st.subheader('Advanced Settings')
    client_interface = text_input_client_interface()
    server_interface = text_input_server_interface()
    local_output_directory = text_input_local_output_directory()

    update_widget('')
    # Button to start the tests
    if st.form_submit_button('Run Tests'):
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
            local_output_directory=local_output_directory
        )
        config.write_yaml()

        logger = get_logger(__name__)
        handler = StreamlitLogHandler(st.empty().code)
        logger.addHandler(handler)
        if checkbox_generate_pcap:
            ts.generate_pcap(config, logger)
        if checkbox_execute_test_cases:
            execute_test_cases(config, logger, markers)

