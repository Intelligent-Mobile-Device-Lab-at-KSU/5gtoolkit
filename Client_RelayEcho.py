# Client_RelayEcho.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app measures the Layer 7 delay to send the character '0' to the UDP echo server.
# The purpose of this app is to measure the Layer 7 round trip time from this phone to the echo server.

# The intended use is to run this app in Termux.
# Provide the number of times you would like to run this application.
# Statistics will be returned to you.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that server ip and port are correct.
# 4. python Client_RelayEcho.py <number of measurements>

import socket
import sys
import signal
import time
import json
f = open('config.json',)
conf = json.load(f)
f.close()

NumTimesToRun = int(sys.argv[1])

pktnumber=0
delays = []

server_addr = (conf["echo_server"]["ip"], conf["echo_server"]["port"])

udpClientSock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def signal_handler(sig, frame):
    udpClientSock.close()
    print('\n')
    print("%d bytes sent and received!\n" % (pktnumber))
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print('Sending Packets')
while (pktnumber < NumTimesToRun):
    udpClientSock.sendto(str.encode("0"), server_addr)
    t = time.time()
    data = udpClientSock.recvfrom(1024)
    elapsed = time.time() - t
    delays.append(elapsed)
    pktnumber += 1

udpClientSock.close()
mu = sum(delays) / len(delays)
variance = sum([((x - mu) ** 2) for x in delays]) / len(delays)
stddev = variance ** 0.5

print("Completed %s measurements" % (pktnumber))
print("Average: " + str(mu*1000) + "ms")
print("Std.Dev: " + str(stddev*1000) + "ms")

multiplied_delays = [element * 1000 for element in delays]
print("Min: " + str(min(multiplied_delays)) + "ms")
print("Max: " + str(max(multiplied_delays)) + "ms")
