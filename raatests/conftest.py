# content of conftest.py
import pytest
import os
import sys
from typing import List
from scapy.all import Radius
import logging
from extra_funcs import get_metadata_loc, get_pcap_loc, get_metadata, Metadata
from fpdf import FPDF

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import raatestbed.pcap_extract as pe


def pytest_addoption(parser):
    parser.addoption(
        "--pcap_dir",
        action="store",
        default="/usr/local/raa/pcap",
        help="Directory to find PCAP and metadata files",
    )
    parser.addoption(
        "--report_dir",
        action="store",
        default="/usr/local/raa/reports",
        help="Directory to store reports",
    )
    parser.addoption(
        "--test_name",
        action="store",
        required=True,
        help="Name of test",
    )


class CustomPDFReportPlugin:
    def __init__(self):
        self.test_results = []

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            possible_markers = set(pytest.mark._markers)
            test_keywords = set(report.keywords)
            test_markers = list(possible_markers & test_keywords)
            self.test_results.append(
                (test_markers, report.nodeid, report.outcome, report.capstdout)
            )

    def pytest_sessionfinish(self, session):
        report_dir = session.config.getoption("--report_dir")
        test_name = session.config.getoption("--test_name")
        pdf = FPDF(orientation="L")
        pdf.add_page()

        # Create a title
        pdf.set_font("Arial", size=14)
        pdf.cell(200, 10, f'Test Report for "{test_name}"', ln=1, align="C")
        pdf.ln()
        pdf.ln()

        # Common setup for all cells
        pdf.set_font("Arial", size=10)
        cell_height = 10
        whitespace = 3

        # Create headers
        markers_title = "Marker(s)"
        category_title = "Category"
        test_case_title = "Test Case"
        result_title = "Result"
        test_file_title = "File"
        context_title = "Context"

        # Get list of all cell values to calculate max width
        markers_list = [markers_title]
        category_list = [category_title]
        test_case_list = [test_case_title]
        result_list = [result_title]
        test_file_list = [test_file_title]
        context_list = [context_title]

        for markers, test, result, context in self.test_results:
            split_test = test.split("::")
            markers_str = ", ".join(markers)
            if len(split_test) == 2:
                test_file, test_case = split_test
                category = ""
            else:
                assert len(split_test) == 3
                test_file, category, test_case = split_test

            markers_list.append(markers_str)
            category_list.append(category)
            test_case_list.append(test_case)
            context_list.append(context)
            test_file_list.append(test_file)
            result_list.append(result.upper())

        # Get max width for each column
        def get_max_width(cell):
            return max([pdf.get_string_width(text) for text in cell])

        width_markers = get_max_width(markers_list)
        width_category = get_max_width(category_list)
        width_test_case = get_max_width(test_case_list)
        width_result = get_max_width(result_list)
        width_test_file = get_max_width(test_file_list)
        width_context = get_max_width(context_list)

        # Write data to table
        for marker, category, test_case, result, test_file, context in zip(
            markers_list,
            category_list,
            test_case_list,
            result_list,
            test_file_list,
            context_list,
        ):
            pdf.cell(width_markers + whitespace, cell_height, marker, border=1)
            pdf.cell(width_category + whitespace, cell_height, category, border=1)
            pdf.cell(width_test_case + whitespace, cell_height, test_case, border=1)

            # Set color based on result, red=failed, green=passed
            if result.lower() == "passed":
                pdf.set_text_color(0, 128, 0)
            if result.lower() == "failed":
                pdf.set_text_color(128, 0, 0)
            pdf.cell(width_result + whitespace, cell_height, result, border=1)

            pdf.set_text_color(0, 0, 0)
            pdf.cell(width_test_file + whitespace, cell_height, test_file, border=1)
            pdf.cell(width_context + whitespace, cell_height, context, border=1)
            pdf.ln()

        # Write PDF to file
        report_fullpath = os.path.join(report_dir, f"{test_name}_report.pdf")
        logging.info(f"Writing report to {report_fullpath}")
        pdf.output(report_fullpath)
        logging.info(f"Report written to {report_fullpath}")


def pytest_configure(config):
    """Do preliminary checks to ensure there are PCAP and metadata files before test execution. Also load plugins."""
    test_name = config.getoption("--test_name")
    pcap_dir = config.getoption("--pcap_dir")
    config.addinivalue_line("markers", "core: basic tests")
    config.addinivalue_line("markers", "core_upload: basic tests for upload")
    config.addinivalue_line("markers", "core_download: basic tests for download")
    config.addinivalue_line("markers", "openroaming: openroaming tests")
    # These functions will raise errors if the files are not found
    _ = get_metadata_loc(test_name, pcap_dir)
    _ = get_pcap_loc(test_name, pcap_dir)
    config.pluginmanager.register(CustomPDFReportPlugin())


def pytest_unconfigure(config):
    """Unload plugins."""
    plugin = config.pluginmanager.get_plugin(CustomPDFReportPlugin)
    if plugin is not None:
        config.pluginmanager.unregister(plugin)


@pytest.fixture
def metadata(request) -> Metadata:
    """Return metadata for a given test name."""
    test_name = request.config.getoption("--test_name")
    directory = request.config.getoption("--pcap_dir")
    return get_metadata(test_name, directory)


@pytest.fixture
def packets(request) -> List[Radius]:
    """Return relevant packets from PCAP file."""
    test_name = request.config.getoption("--test_name")
    directory = request.config.getoption("--pcap_dir")
    metadata = get_metadata(test_name, directory)
    username = metadata.username
    pcap_loc = get_pcap_loc(test_name, directory)
    pcap = pe.get_relevant_packets(pcap_loc, username)
    return pcap
