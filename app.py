import streamlit as st
import sys
import webbrowser
import raatestbed.test_setup as ts
from typing import List
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

def checkbox_select_test_parts():
    """Checkbox to select which parts of the test to run"""
    generate_pcap = st.checkbox("Generate PCAP")
    generate_report = st.checkbox("Generate Report")
    return generate_pcap, generate_report

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

def links():
    if st.button("Go to Google"):
        webbrowser.open_new_tab("https://www.google.com")

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
    # PCAP generation + report selection
    generate_pcap, generate_report = checkbox_select_test_parts()
    # Marker Selection
    markers = get_selected_markers(TEST_TAGS)

    # Advanced Settings
    st.subheader('Advanced Settings')
    client_interface = text_input_client_interface()
    server_interface = text_input_server_interface()
    local_output_directory = text_input_local_output_directory()

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
            generate_pcap=generate_pcap,
            generate_report=generate_report,
            markers=markers,
            client_interface=client_interface,
            server_interface=server_interface,
            local_output_directory=local_output_directory
        )
        config.write_yaml()

        # Redirect stdout to capture print output
        original_stdout = sys.stdout
        if generate_pcap:
            ts.generate_pcap(config)

        #st.write(f'Starting tests with Chunk Size: {chunk_size}, Number of Chunks: {chunks}')
        #for marker in markers:
        #    st.write(f'Running {marker} tests...')

