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
import threading
import random
import string

f = open('config.json', )
conf = json.load(f)
f.close()

server_addr = (conf["relay_server"]["ip"], conf["relay_server"]["port"])

udpServerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpServerSock.bind(server_addr)
print("Relay server listening on " + server_addr[0] + ":" + str(server_addr[1]))


def signal_handler(sig, frame):
    udpServerSock.close()
    print('\n')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

noHalt = True
server_halt_addr = (conf["relay_server"]["ip"], conf["relay_server"]["halt_port"])

# Create a datagram socket
UDPServerSocket_halt = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPServerSocket_halt.bind(server_halt_addr)


# This function is called in a separate thread for listening
# for any halt commands sent from the phone in case the Server gets caught in a while loop.
def UDPServerSocket_halt_listener():
    global noHalt
    while True:
        bytesAddressPair = UDPServerSocket_halt.recvfrom(1024)
        message = bytesAddressPair[0]
        if message.decode() == "0":
            UDPServerSocket_halt.sendto(str("1").encode(),bytesAddressPair[1])
            if not noHalt:
                noHalt = not noHalt
        time.sleep(.05)


# Set up thread for UDP Server (phone is pushing as client to RPI)
th_halt_udp = threading.Thread(name='UDPServerSocket_halt_listener', target=UDPServerSocket_halt_listener, args=())
th_halt_udp.start()

while True:
    data, client_addr = udpServerSock.recvfrom(1024)
    data_ctrl_msg = data.decode().split(":")
    if data_ctrl_msg[0] == "GDR" or data_ctrl_msg[0] == "DJ":
        print("Initiating " + data_ctrl_msg[0] + "...")
        pktnumber = 0
        pktSize = int(data_ctrl_msg[1])
        duration = int(data_ctrl_msg[2])
        t = time.time()
        while (time.time() - t) <= duration:
            s = ''.join(random.choice(string.digits) for _ in range(pktSize))
            udpServerSock.sendto(s.encode(), client_addr)
            pktnumber += 1
        o = "done:" + str(pktnumber)
        udpServerSock.sendto(o.encode(), client_addr)
        print(data_ctrl_msg[0] + " done.")
        print("Listening...")

    if data_ctrl_msg[0] == "UGR":
        print("Initiating UGR...")
        packetSizeInBytes = int(data_ctrl_msg[1])
        respFromUploader = ''
        totalBytesRecvd = 0
        udpServerSock.settimeout(3)
        udpServerSock.sendto(str.encode("OK"), client_addr)
        while ("done" not in respFromUploader) and noHalt:
            try:
                respFromUploader = udpServerSock.recvfrom(packetSizeInBytes)
            except:
                noHalt = not noHalt
                break
            respFromUploader = respFromUploader[0].decode()
            totalBytesRecvd += len(respFromUploader)

        udpServerSock.settimeout(None)
        print("UGR getting stats...")
        if not noHalt:
            print("Halted.")
            print("Listening...")
            continue

        numberOfPackets = totalBytesRecvd / packetSizeInBytes
        ojson = {
            "totalBytesRecvd": totalBytesRecvd,
            "numberOfPackets": numberOfPackets
        }

        udpServerSock.sendto(json.dumps(ojson).encode(), client_addr)
        print("UGR done.")
        print("Listening...")

    if data_ctrl_msg[0] == "JU":
        print("Initiating JU...")
        packetSizeInBytes = int(data_ctrl_msg[1])
        respFromUploader = ''
        totalBytesRecvd = 0
        epochs = []
        udpServerSock.settimeout(3)
        udpServerSock.sendto(str.encode("OK"), client_addr)
        while ("done" not in respFromUploader) and noHalt:
            try:
                respFromUploader = udpServerSock.recvfrom(packetSizeInBytes)
            except:
                noHalt = not noHalt
                break
            epochs.append(time.time())
            respFromUploader = respFromUploader[0].decode()

        udpServerSock.settimeout(None)
        print("JU getting stats...")
        if not noHalt:
            print("Halted.")
            print("Listening...")
            continue

        # Calculate Jitter
        errorStatus = False
        i = 0
        delays = []
        L = len(epochs)
        while i <= L - 2:
            delays.append(epochs[i + 1] - epochs[i])
            i += 1

        if len(delays) == 0:
            errorStatus = True
            mu = -1
            stddev = -1
            themin = -1
            themax = -1
        else:
            mu = sum(delays) / len(delays)
            variance = sum([((x - mu) ** 2) for x in delays]) / len(delays)
            stddev = variance ** 0.5
            multiplied_delays = [element * 1000 for element in delays]
            themin = min(multiplied_delays)
            themax = max(multiplied_delays)

        ojson = {
            "error": errorStatus,
            "avg": mu * 1000,
            "stddev": stddev * 1000,
            "min": themin,
            "max": themax
        }
        udpServerSock.sendto(json.dumps(ojson).encode(), client_addr)
        print("JU done.")
        print("Listening...")
