
from src.files import init_dirs, SUBDIRS, get_marker_list
import src.files as files
import os

def test_init_dirs():
    """Test subdirectories are created."""
    root_dir = "/tmp/raatest"
    init_dirs(root_dir=root_dir)
    for _, subdir in SUBDIRS.items():
        assert os.path.exists(os.path.join(root_dir, subdir))

def test_get_marker_list():
    """Test correct markers are read from pytest.ini file."""
    expected_markers = ["marker_a", "marker_b", "marker_c", "marker_d"]
    markers = get_marker_list(ini_file="tests/data/configs/pytest.ini")
    assert len(markers) == len(expected_markers)
    for expected_marker in expected_markers:
        assert expected_marker in markers

def test_file_creation():
    """Test files can be created in subdirectories."""
    root_dir = "/tmp/raatest2"
    test_name = "test"
    init_dirs(root_dir=root_dir)
    files_to_create = [
        files.get_metadata_filename(test_name=test_name, root_dir=root_dir),
        files.get_pcap_filename(test_name=test_name, root_dir=root_dir),
        files.get_report_filename(test_name=test_name, root_dir=root_dir),
        files.get_config_filename(test_name=test_name, root_dir=root_dir),
        files.get_freeradius_log_filename(test_name=test_name, root_dir=root_dir),
        files.get_wpasupplicant_log_filename(test_name=test_name, root_dir=root_dir),
        files.get_tcpdump_log_filename(test_name=test_name, root_dir=root_dir),
        files.get_zipped_bundle_filename(test_name=test_name, root_dir=root_dir),
    ]
    # Create files
    for file in files_to_create:
        with open(file, "w") as f:
            f.write("test")