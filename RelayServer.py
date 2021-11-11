# RelayServer.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app receives control messages from a client and performs the request.
# a. Client Sends: GDP:100:60, the RelayServer will stream 100 byte packets for 60 seconds.

# The purpose of this app is to measure the Layer 7 one-way Goodput from relay server to client.

# The intended use is to run this app on a server.

# 1. Log into your server.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that relay server ip and port are what you desire.
# 4. python3 RelayServer.py

import socket
import sys
import signal
import json
import time
import random
import string

f = open('config.json',)
conf = json.load(f)
f.close()

server_addr = (conf["relay_server"]["ip"], conf["relay_server"]["port"])

udpServerSock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpServerSock.bind(server_addr)
print("Relay server listening on " + server_addr[0] + ":" + str(server_addr[1]))

def signal_handler(sig, frame):
    udpServerSock.close()
    print('\n')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

while True:
    data, client_addr = udpServerSock.recvfrom(1024)
    data_ctrl_msg = data.decode().split(":")
    if data_ctrl_msg[0]=="GDR":
        print("Initiating GDR...")
        pktnumber = 0
        pktSize = int(data_ctrl_msg[1])
        duration = int(data_ctrl_msg[2])
        t = time.time()
        while (time.time() - t) <= duration:
            s = ''.join(random.choice(string.digits) for _ in range(pktSize))
            udpServerSock.sendto(s.encode(), client_addr)
            pktnumber += 1
        o = "done:"+str(pktnumber)
        udpServerSock.sendto(o.encode(), client_addr)
        print("GDR done.")
        print("Listening...")
    if data_ctrl_msg[0]=="UGR":
        print("Initiating UGR...")
        packetSizeInBytes = int(data_ctrl_msg[1])
        udpServerSock.sendto(str.encode("OK"), client_addr)
        respFromUploader = ''
        totalBytesRecvd = 0
        while "done" not in respFromUploader:
            respFromUploader = udpServerSock.recvfrom(packetSizeInBytes)
            respFromUploader = respFromUploader[0].decode()
            totalBytesRecvd += len(respFromUploader)

        numberOfPackets = totalBytesRecvd / packetSizeInBytes
        ojson = {
            "totalBytesRecvd" : totalBytesRecvd,
            "numberOfPackets" : numberOfPackets
        }

        udpServerSock.sendto(json.dumps(ojson).encode(), client_addr)
        print("UGR done.")
        print("Listening...")
