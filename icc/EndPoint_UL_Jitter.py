# EndPoint_UL_Jitter.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app measures the Layer 7 one-way jitter from the phone to the UDP relay server.
# The phone will send a message to the relay server asking to prepare for a one-way stream of bytes from the phone.
# The phone will stream the bytes according to the users desires.
# The relay server will report the statistics.

# The intended use is to run this app in Termux.
# Provide the size of each message, and the duration of the test in seconds.
# Statistics will be returned to you.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that relay server ip and port are correct.
# 4. python EndPoint_UL_Jitter.py <size of packets in bytes> <duration of measurement in seconds>

import socket
import sys
import signal
import time
import json
import random
import string

f = open('config.json',)
conf = json.load(f)
f.close()

packetSizeInBytes_String = sys.argv[1]
packetSizeInBytes = int(packetSizeInBytes_String)
durationOfTestInSeconds_String = sys.argv[2]
durationOfTestInSeconds = int(durationOfTestInSeconds_String)

totalBytesSent = 0

server_addr = (conf["relay_server"]["ip"], conf["relay_server"]["port"])
server_halt_addr = (conf["relay_server"]["ip"], conf["relay_server"]["halt_port"])

udpClientSock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def signal_handler(sig, frame):
    udpClientSock.sendto(str("0").encode(), server_halt_addr)
    data = udpClientSock.recvfrom(1024)
    if data[0].decode() == "1":
        udpClientSock.close()
        print('\n')
        sys.exit(0)
    else:
        udpClientSock.close()
        print('ERROR Could Not Stop Server \n')
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print('Sending JU Request to Relay Server...')
udpClientSock.sendto(str.encode("JU:"+packetSizeInBytes_String), server_addr)
respFromServer = udpClientSock.recvfrom(65507)
print('Server ready.')
print('Measurement in progress...')
totalPacketsSent = 0
t = time.time()
while (time.time() - t) <= durationOfTestInSeconds:
    s = ''.join(random.choice(string.digits) for _ in range(packetSizeInBytes))
    udpClientSock.sendto(s.encode(), server_addr)
    totalPacketsSent += 1

print("Done. Awaiting Stats From Relay Server...")
udpClientSock.sendto(str.encode("done"), server_addr)
respFromServer = udpClientSock.recvfrom(1024)
stats = json.loads(respFromServer[0].decode())
udpClientSock.close()

if stats["error"]:
    print("Divide by zero error at the Server. Maybe decrease the packet size? Try again.")
else:
    print("Stats Received.")
    print("Phone attempted to send %s packets" % (totalPacketsSent))
    print("Jitter average: " + str(stats["avg"]) + "ms")
    print("Jitter std.dev: " + str(stats["stddev"]) + "ms")
    print("Jitter min: " + str(stats["min"]) + "ms")
    print("Jitter max: " + str(stats["max"]) + "ms")
