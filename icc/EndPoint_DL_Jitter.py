# EndPoint_DL_Jitter.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app measures the Layer 7 jitter from the UDP relay server.
# The phone will send a message to the relay server asking for a one-way stream of bytes to the phone.
# The UDP relay server will stream the bytes according to the users desires.

# The intended use is to run this app in Termux.
# Provide the size of each message, and the duration of the test in seconds.
# Statistics will be returned to you.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that relay server ip and port are correct.
# 4. python EndPoint_DL_Jitter.py <size of packets in bytes> <duration of measurement in seconds>

import socket
import sys
import signal
import time
import json
f = open('config.json',)
conf = json.load(f)
f.close()

packetSizeInBytes_String = sys.argv[1]
packetSizeInBytes = int(packetSizeInBytes_String)
durationOfTestInSeconds_String = sys.argv[2]
durationOfTestInSeconds = int(durationOfTestInSeconds_String)

totalBytesRecvd = 0
epochs = []

server_addr = (conf["relay_server"]["ip"], conf["relay_server"]["port"])

udpClientSock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def signal_handler(sig, frame):
    udpClientSock.close()
    print('\n')
    print("%d bytes received!\n" % (totalBytesRecvd))
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print('Sending DJ Request to Relay Server...')
udpClientSock.sendto(str.encode("DJ:"+packetSizeInBytes_String+":"+durationOfTestInSeconds_String), server_addr)
print('Server ready.')
print('Measurement in progress...')
respFromServer = ''
while "done" not in respFromServer:
    respFromServer = udpClientSock.recvfrom(65507)
    epochs.append(time.time())
    respFromServer = respFromServer[0].decode()

udpClientSock.close()
totalPacketsSent = int(respFromServer.split(":")[1])
print('Done.')

# Calculate Jitter
i = 0
delays = []
L = len(epochs)
while i <= L-2:
    delays.append(epochs[i+1]-epochs[i])
    i += 1

if len(delays) == 0:
    print("Divide by zero error. Maybe decrease the packet size? Try again.")
else:
    mu = sum(delays) / len(delays)
    variance = sum([((x - mu) ** 2) for x in delays]) / len(delays)
    stddev = variance ** 0.5
    multiplied_delays = [element * 1000 for element in delays]
    themin = min(multiplied_delays)
    themax = max(multiplied_delays)

    print("Server attempted to send %s packets" % (totalPacketsSent))
    print("Jitter average: " + str(mu*1000) + "ms")
    print("Jitter std.dev: " + str(stddev*1000) + "ms")
    print("Jitter min: " + str(themin) + "ms")
    print("Jitter max: " + str(themax) + "ms")
