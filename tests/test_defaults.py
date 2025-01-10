import pytest
import src.defaults as defaults

@pytest.fixture()
def cliargs():
    cliargs = {
      defaults.KEY_SERVER_IFACE: "eth_fron_cli",
      defaults.KEY_CLIENT_IFACE: "wlan_from_cli",
      defaults.KEY_SSID: "ssid_from_cli",
      defaults.KEY_GENERATE_PCAP: True,
      defaults.KEY_DOWNLOAD_CHUNKS: True,
    }
    return cliargs

@pytest.fixture()
def configargs():
    configargs = {
      defaults.KEY_SERVER_IFACE: "eth_fron_config",
      defaults.KEY_CLIENT_IFACE: "wlan_from_config",
      defaults.KEY_SSID: "ssid_from_config",
      defaults.KEY_GENERATE_PCAP: False,
      defaults.KEY_DOWNLOAD_CHUNKS: False,
      defaults.KEY_RELATIVE_PYTEST_INI: "ini_from_config",
      defaults.KEY_DATA_SERVER_IP: "ip_from_config",
    }
    return configargs

def test_arg_presense(cliargs, configargs):
  default_args = defaults.get_defaults()
  final = defaults.get_all_args(cliargs, configargs)
  #Check if all keys are present
  for key in default_args.keys():
    assert key in final.keys()

def test_arg_priority(cliargs, configargs):
  """Test combination of args."""
  #Priority: CLI > Config > Default
  default_args = defaults.get_defaults()
  final = defaults.get_all_args(cliargs, configargs)

  #CLI args should take priority over both config and default args
  assert final[defaults.KEY_SERVER_IFACE] == cliargs[defaults.KEY_SERVER_IFACE]
  assert final[defaults.KEY_CLIENT_IFACE] == cliargs[defaults.KEY_CLIENT_IFACE]
  assert final[defaults.KEY_SSID] == cliargs[defaults.KEY_SSID]
  assert final[defaults.KEY_GENERATE_PCAP] == cliargs[defaults.KEY_GENERATE_PCAP]
  assert final[defaults.KEY_DOWNLOAD_CHUNKS] == cliargs[defaults.KEY_DOWNLOAD_CHUNKS]

  #Config args should take priority over default
  assert final[defaults.KEY_DATA_SERVER_IP] == configargs[defaults.KEY_DATA_SERVER_IP]
  assert final[defaults.KEY_RELATIVE_PYTEST_INI] == configargs[defaults.KEY_RELATIVE_PYTEST_INI]

  #Default args should be used if not provided in CLI or config
  assert final[defaults.KEY_CHUNK_SIZE] == default_args[defaults.KEY_CHUNK_SIZE]
  assert final[defaults.KEY_CHUNKS] == default_args[defaults.KEY_CHUNKS]
