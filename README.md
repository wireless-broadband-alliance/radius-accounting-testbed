# Self-Certification Test Bed for WBA RADIUS Accounting Assurance Project
This is a self-certification test bed for the WBA RADIUS Accounting Assurance Project.

## Markers
Markers are used to categorize the tests. The following markers are used:

| Marker    | Description |
| -------- | ------- |
| core | Basic RADIUS tests for RFC compliance |
| core-upload | Basic RADIUS tests for file upload |
| core-download | Basic RADIUS tests for file download |
| openroaming | OpenRoaming tests |

## Basic Operation
This test bed will do the following:

1. Control an end-to-end 802.1X/RADIUS authentication+accounting test, running a packet capture in the process.
2. Get supplicant to transfer a large amount of data.
3. Extract fields from the RADIUS packet capture to run a series of accounting tests (see below for test cases).

## Test Cases
### Attribute Checks
Purpose is to test behavior a presence of attributes

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

Run Pytest:
```bash
pytest -v -k -m <marker_name> raatests
```
where `<marker_name>` is the marker name (e.g., `core`, `core-upload`, `core-download`, `openroaming`).

