from appcli import convert_markers

def test_marker_to_list():
    """Test marker string to list."""
    markers_str1 = "core, smoke, sanity"
    markers_str2 = "core smoke sanity"
    markers_str3 = "core ; smoke       ; sanity"
    for markers_str in [markers_str1, markers_str2, markers_str3]:
        markers_list = convert_markers(markers_str)
        assert markers_list == ["core", "smoke", "sanity"]