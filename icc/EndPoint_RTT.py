# EndPoint_RTT.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app measures the Layer 7 delay to send a packet to the UDP EndPointServer.
# The purpose of this app is to measure the Layer 7 round trip time from this phone to the EndPointServer.

# The intended use is to run this app in Termux.
# Provide the number of times you would like to run this application.
# Statistics will be returned to you.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that end point server ip and port are correct.
# 4. python EndPoint_RTT.py <pktsize> <#ofpackets>

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

if len(sys.argv) == 3:
    pktsize_str = sys.argv[1]
    pktsize = int(pktsize_str)
    NumTimesToRun = int(sys.argv[2])
else:
    print('Not enough arguments, \nusage: python EndPoint_RTT.py <pktsize> <#ofpackets>')
    sys.exit(0)

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
print('Sending ECHO Request to EndPointServer...')
udpClientSock.sendto(str.encode("ECHO:"+pktsize_str), server_addr)
respFromServer = udpClientSock.recvfrom(65507)
print('Server ready.')
print('Measurement in progress...')

while (pktnumber < NumTimesToRun):
    s = ''.join(random.choice(string.digits) for _ in range(pktsize))
    udpClientSock.sendto(s.encode(), server_addr)
    t = time.time()
    data = udpClientSock.recvfrom(65507)
    elapsed = time.time() - t
    delays.append(elapsed)
    pktnumber += 1

udpClientSock.sendto(str.encode("ECHO:finish"), server_addr)
udpClientSock.close()

if len(delays) == 0:
    print("Divide by zero error. Maybe decrease the packet size? Try again.")
else:
    mu = sum(delays) / len(delays)
    variance = sum([((x - mu) ** 2) for x in delays]) / len(delays)
    stddev = variance ** 0.5
    multiplied_delays = [element * 1000 for element in delays]
    themin = min(multiplied_delays)
    themax = max(multiplied_delays)

    print("Completed %s measurements" % (pktnumber))
    print("Average: " + str(mu*1000) + "ms")
    print("Std.Dev: " + str(stddev*1000) + "ms")
    print("Min: " + str(themin) + "ms")
    print("Max: " + str(themax) + "ms")
