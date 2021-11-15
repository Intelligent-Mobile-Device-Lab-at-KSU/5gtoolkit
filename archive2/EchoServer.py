# EchoServer.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app receives character '0' and echos it back to the UDP client.
# The purpose of this app is to measure the Layer 7 round trip time from this phone to the echo server.

# The intended use is to run this app on a server.

# 1. Log into your server.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that echo server ip and port are what you desire.
# 3. python EchoServer.py

import socket
import sys
import signal
import json
f = open('config.json',)
conf = json.load(f)
f.close()

pktnumber = 0

server_addr = (conf["echo_server"]["ip"], conf["echo_server"]["port"])

udpServerSock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpServerSock.bind(server_addr)
print("Echo server listening on " + server_addr[0] + ":" + str(server_addr[1]))

def signal_handler(sig, frame):
    udpServerSock.close()
    print('\n')
    print("%d bytes received!\n" % (pktnumber))
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

while True:
    data, client_addr = udpServerSock.recvfrom(1)
    udpServerSock.sendto(data, client_addr)
    pktnumber += 1
