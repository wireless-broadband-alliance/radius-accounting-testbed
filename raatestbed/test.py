from data_transfer import TCPServer
import time
import logging

# set up basic logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
#
## Specify the network interface you want to monitor (e.g., 'eth0')
# network_interface = "wlp35s0f0"

# server = TCPServer("192.168.1.205", 9000, 9000, 1000, 1000)
# server.start(download=True)
# time.sleep(5)
# server.transfer_data()

# server = TCPServer("127.0.0.1", 9000, 9000, 1000, 1000, "lo")
server = TCPServer("127.0.0.1", 9000, 9000, 1000, 10, "lo")
server.start(download=True)
time.sleep(5)
counter = server.transfer_data()
print(counter.to_dict())
