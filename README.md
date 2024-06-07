# Self-Certification Test Bed for WBA RADIUS Accounting Assurance Project

This is a self-certification test bed for the WBA RADIUS Accounting Assurance Project.

## Overview

This test bed is designed to run a series of RADIUS tests from a range of categories (see below). The focus of the tests is to verify that the RADIUS-based NAS is compliant with the RADIUS protocol and conforms to best practices. However, the primary goal of this test bed is to verify the usage data reported in accounting is accurate.

## Basic Operation

This test bed will do the following:

1. Control an end-to-end 802.1X/RADIUS authentication+accounting test, running a packet capture in the process.
2. Get supplicant to transfer a large amount of data.
3. Extract fields from the RADIUS packet capture (PCAP) to run a series of accounting tests. See below for test cases.

## Markers

Markers are used to specify the tests to run against the PCAP. The following markers are currently used:

| Test Category    | Marker | Description |
| -------- | -------- | ------- |
| core | `core` | Basic RADIUS tests for RFC compliance |
| core | `core-upload` | Basic RADIUS tests for file upload |
| core | `core-download` | Basic RADIUS tests for file download |
| openroaming | `openroaming` | OpenRoaming tests |

## Test Cases

### Attribute Checks

#### Core Tests

Purpose is check RFC compliance through attributes.

Markers: `core`, `core-upload`, `core-download`

#### Test Cases for Attribute Checks

1. Unique and persistent Acct-Session-Id in accounting sessions.
2. Acct-Session-Id is persistent in authentication and accounting sessions.
3. Start, Update, and Stop records are present in accounting session.
4. One Start and Stop record (two Stops reporting different values?).
5. Stop record is last message in accounting session
6. Stop record contains highest usage fields.
7. At least 3 Class attributes are echoed.
8. Persistent CUI is echoed.
9. Acct-Input-Gigaword rolls over.
10. Acct-Output-Gigaword rolls over.

### Accuracy Checks

Purpose is to verify reported attribute values are accurate.

#### Test Cases for Accuracy Checks

1. Input tonnage is accurate.
2. Output tonnage is accurate.
3. Session duration is accurate.
4. Input packet count is non-zero.
5. Output packet count is non-zero.

### Run Demo

#### Basic Usage

```bash
python3 app.py <test_name> <data_download_ip> <data_download_port>
```

#### Help

```bash
python3 app.py --help
```

#### All Possible Options

There are several options available to the user. The following is the help output:

```bash
usage: app.py [-h] [--interface INTERFACE] [--debug] [--data_server_listen_port DATA_SERVER_LISTEN_PORT] [--logs_dir LOGS_DIR] [--pcap_dir PCAP_DIR]
              [--chunk_size CHUNK_SIZE] [--chunks CHUNKS] [--ssid SSID] [--wireless_interface WIRELESS_INTERFACE]
              [--wired_interface WIRED_INTERFACE]
              test_name data_server_ip data_server_port

positional arguments:
  test_name             Name of the test to run
  data_server_ip        IP of the server to get data from
  data_server_port      Port of the server to get data from

options:
  -h, --help            show this help message and exit
  --interface INTERFACE
                        Interface used to get data from (default: wlan0)
  --debug
  --data_server_listen_port DATA_SERVER_LISTEN_PORT
                        default: 8000
  --logs_dir LOGS_DIR   default: /usr/local/raa/logs
  --pcap_dir PCAP_DIR   default: /usr/local/raa/pcap
  --chunk_size CHUNK_SIZE
                        default: 1048576
  --chunks CHUNKS       Number of chunks to pull, default: 1
  --ssid SSID           default: raatest
  --wireless_interface WIRELESS_INTERFACE
                        default: wlan0
  --wired_interface WIRED_INTERFACE
                        default: eth0
```

#### Installation

Make sure you have the required packages installed (see below).

1. Python3
2. Pip
3. Python virtualenv (optional but recommended)

Clone this repository and navigate to the root directory.

Create the virtual environment:

```bash
python3 -m venv env
```

Activate the virtual environment:

```bash
source env/bin/activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```
