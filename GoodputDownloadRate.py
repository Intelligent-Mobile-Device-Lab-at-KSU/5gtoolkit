# GoodputDownloadRate.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app measures the Layer 7 Goodput from the UDP relay server.
# The phone will send a message to the relay server asking for a one-way stream of bytes to the phone.
# The UDP relay server will stream the bytes according to the users desires.

# The intended use is to run this app in Termux.
# Provide the size of each message, and the duration of the test in seconds.
# Statistics will be returned to you.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that relay server ip and port are correct.
# 4. python GoodputDownloadRate.py <size of packets in bytes> <duration of measurement in seconds>

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

server_addr = (conf["relay_server"]["ip"], conf["relay_server"]["port"])

udpClientSock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def signal_handler(sig, frame):
    udpClientSock.sendto(str.encode("GDR:STOP"), server_addr)
    udpClientSock.close()
    print('\n')
    print("%d bytes received!\n" % (totalBytesRecvd))
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print('Sending Request to Relay Server...')
udpClientSock.sendto(str.encode("GDR:"+packetSizeInBytes_String+":"+durationOfTestInSeconds_String), server_addr)
respFromServer = udpClientSock.recvfrom(1024)
print('Server ready.')
while "done" not in respFromServer:
    respFromServer = udpClientSock.recvfrom(packetSizeInBytes)
    totalBytesRecvd += len(respFromServer)

totalPacketsSent = respFromServer.split(":")[1]
print("Last message from Server: " + respFromServer)
udpClientSock.close()
goodput = totalBytesRecvd/durationOfTestInSeconds
numberOfPackets = totalBytesRecvd/packetSizeInBytes
packetReceptionRate = (numberOfPackets/totalPacketsSent)*100

print("Goodput (Megabitsps): %s " % ((goodput/8)/(1e6)))
print("Goodput (MegaBytesps): %s " % ((goodput)/(1e6)))
print("Number of Packets Received: " + str(numberOfPackets))
print("Packet Reception Rate: " + str(packetReceptionRate) + "%")
