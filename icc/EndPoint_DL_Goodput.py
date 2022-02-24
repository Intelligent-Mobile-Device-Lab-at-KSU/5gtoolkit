# EndPoint_DL_Goodput.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app measures the Layer 7 Goodput from the UDP EndPointServer.
# The phone will send a message to the EndPointServer asking for a one-way stream of bytes to the phone.
# The UDP EndPointServer will stream the bytes according to the users desires.

# The intended use is to run this app in Termux.
# Provide the size of each message, and the duration of the test in seconds.
# Statistics will be returned to you.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that EndPointServer ip and port are correct.
# 4. python EndPoint_DL_Goodput.py <size of packets in bytes> <duration of measurement in seconds>

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

server_addr = (conf["endpoint_server"]["ip"], conf["endpoint_server"]["port"])

udpClientSock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def signal_handler(sig, frame):
    udpClientSock.close()
    print('\n')
    print("%d bytes received!\n" % (totalBytesRecvd))
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print('Sending EDG Request to EndPointServer...')
udpClientSock.sendto(str.encode("EDG:"+packetSizeInBytes_String+":"+durationOfTestInSeconds_String), server_addr)
print('EndPointServer ready.')
print('Measurement in progress...')
respFromServer = ''
while "done" not in respFromServer:
    respFromServer = udpClientSock.recvfrom(65507)
    respFromServer = respFromServer[0].decode()
    totalBytesRecvd += len(respFromServer)

print('Done.')
udpClientSock.close()
totalPacketsSent = int(respFromServer.split(":")[1])

goodput = totalBytesRecvd/durationOfTestInSeconds
numberOfPackets = totalBytesRecvd/packetSizeInBytes
packetReceptionRate = (numberOfPackets/totalPacketsSent)*100

print("==Endpoint DL Goodput==")
print("EndPointServer Sent: " + str(totalPacketsSent))
print("Goodput (raw): %s bytes" % (goodput))
print("Goodput (Mbps): %s " % ((goodput*8)/(1e6)))
print("Goodput (MegaBytesps): %s " % ((goodput)/(1e6)))
print("Number of Packets Received: " + str(numberOfPackets))
print("Packet Reception Rate: " + str(packetReceptionRate) + "%")
