
import src.files as files
import os

def test_init_dirs():
    files.init_dirs(root_dir="/tmp")
    #check that pcap subdirectory exists in /tmp
    

#def test_get_marker_list