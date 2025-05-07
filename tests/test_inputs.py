import pytest
import src.inputs as inputs

@pytest.fixture()
def cliargs():
    cliargs = {
      inputs.KEY_SERVER_IFACE: "eth_fron_cli",
      inputs.KEY_CLIENT_IFACE: "wlan_from_cli",
      inputs.KEY_SSID: "ssid_from_cli",
      inputs.KEY_GENERATE_PCAP: True,
      inputs.KEY_DOWNLOAD_CHUNKS: True,
      inputs.KEY_TEST_NAME: "does not show because it is a required arg",
      inputs.KEY_RADIUS_PORT: 1234
    }
    return cliargs

@pytest.fixture()
def configargs():
    configargs = {
      inputs.KEY_SERVER_IFACE: "eth_fron_config",
      inputs.KEY_CLIENT_IFACE: "wlan_from_config",
      inputs.KEY_SSID: "ssid_from_config",
      inputs.KEY_GENERATE_PCAP: False,
      inputs.KEY_DOWNLOAD_CHUNKS: False,
      inputs.KEY_RELATIVE_PYTEST_INI: "ini_from_config",
      inputs.KEY_DATA_SERVER_IP: "ip_from_config",
    }
    return configargs

def test_arg_absense(cliargs, configargs):
  """Test no required args are present."""
  final = inputs.get_all_args(cliargs, configargs)
  for reqarg in inputs.get_required_args():
    print(reqarg)
    print(list(final.keys()))
    assert reqarg not in final.keys()

def test_arg_presense(cliargs, configargs):
  """Test all optional args are present."""
  default_args = inputs.get_defaults()
  final = inputs.get_all_args(cliargs, configargs)
  #Check if all keys are present
  for key in default_args.keys():
    assert key in final.keys()

def test_arg_priority(cliargs, configargs):
  """Test combination of args."""
  #Priority: CLI > Config > Default
  default_args = inputs.get_defaults()
  final = inputs.get_all_args(cliargs, configargs)

  #CLI args should take priority over both config and default args
  assert final[inputs.KEY_SERVER_IFACE] == cliargs[inputs.KEY_SERVER_IFACE]
  assert final[inputs.KEY_CLIENT_IFACE] == cliargs[inputs.KEY_CLIENT_IFACE]
  assert final[inputs.KEY_SSID] == cliargs[inputs.KEY_SSID]
  assert final[inputs.KEY_GENERATE_PCAP] == cliargs[inputs.KEY_GENERATE_PCAP]
  assert final[inputs.KEY_DOWNLOAD_CHUNKS] == cliargs[inputs.KEY_DOWNLOAD_CHUNKS]

  #Config args should take priority over default
  assert final[inputs.KEY_RELATIVE_PYTEST_INI] == configargs[inputs.KEY_RELATIVE_PYTEST_INI]

  #Default args should be used if not provided in CLI or config
  assert final[inputs.KEY_CHUNK_SIZE] == default_args[inputs.KEY_CHUNK_SIZE]
  assert final[inputs.KEY_CHUNKS] == default_args[inputs.KEY_CHUNKS]
