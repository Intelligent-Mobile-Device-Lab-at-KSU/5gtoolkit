# PeerGoodputRelay.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app measures the Layer 7 one-way Goodput from this phone to the peer via a RendezvousRelayServer.
# A->RendezvousRelayServer->B (measures Goodput) then B (sends stats back to A)->RendezvousRelayServer->A

# The intended use is to run this app in Termux.
# Provide the number of times you would like to run this application.
# Statistics will be returned to you.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that RendezvousRelayServer server ip and port are correct.
# 4. python PeerGoodputRelay.py <a|b> <size of packets in bytes> <duration of measurement in seconds>
# 5. Example: python PeerGoodputRelay.py a 100 1, means: login as user 'a', send 100 byte packets for 1 second to 'b'
# 6. Example: python PeerGoodputRelay.py b 0 0, means: login as user 'b', receive packets from 'a', send back results
# 7. A is always the sender. B is always the receiver.

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

username = sys.argv[1] # can only be a or b
packetSizeInBytes_String = sys.argv[2]
packetSizeInBytes = int(packetSizeInBytes_String)
durationOfTestInSeconds_String = sys.argv[3]
durationOfTestInSeconds = int(durationOfTestInSeconds_String)

totalBytesSent = 0

server_addr = (conf["rendezvous_relay_server"]["ip"], conf["rendezvous_relay_server"]["port"])
server_halt_addr = (conf["rendezvous_relay_server"]["ip"], conf["rendezvous_relay_server"]["halt_port"])

udpClientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def signal_handler(sig, frame):
    if username=='a':
        udpClientSock.sendto(str.encode("stop"), server_addr)
        udpClientSock.sendto(str.encode("peer_close"), server_addr)
    udpClientSock.close()
    print('\n')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
udpClientSock.sendto(str.encode("checkstatus:" + username), server_addr)
print("Logging In To Rendezvous Relay Server as username: " + username + "...")
respFromServer=''
while ("OK" not in respFromServer):
    udpClientSock.sendto(str.encode("login:" + username), server_addr)
    respFromServer = udpClientSock.recvfrom(1024)
    respFromServer = respFromServer[0].decode()

respFromServer=''
print('Logged in as: '+username+ ", awaiting peer...")
while ("PEER" not in respFromServer):
    respFromServer = udpClientSock.recvfrom(1024)
    respFromServer = respFromServer[0].decode()

udpClientSock.sendto(str.encode("OK"), server_addr)

print("Peer found. Peer Goodput system ready.")

# Device 1 should be logged into rendezvous server as: a
if username == 'a':
    print('Sending Relay Peer Goodput (RPG) Request to Peer...')
    udpClientSock.sendto(str.encode("RPG:" + packetSizeInBytes_String), server_addr)
    while True:
        respFromPeer = udpClientSock.recvfrom(65507)
        respFromPeer = respFromPeer[0].decode()
        if respFromPeer == "keep-alive":
            continue
        elif respFromPeer == "OK":
            print('Peer ready.')
            print("Ensure b displays \"Listening for packets...\" then when ready...")
            break

    x = input("Press any key to begin peer Goodput test through Rendezvous Relay Server...")
    while True:
        print('Measurement in progress...')
        totalPacketsSent = 0
        t = time.time()
        while (time.time() - t) <= durationOfTestInSeconds:
            s = ''.join(random.choice(string.digits) for _ in range(packetSizeInBytes))
            udpClientSock.sendto(s.encode(), server_addr)
            totalPacketsSent += 1

        print("Done. Awaiting Stats From Peer...")
        stats = []
        print("flag0")
        while True:
            print("flag1")
            udpClientSock.sendto(str.encode("peer_finish"), server_addr)
            print("flag2")
            data = udpClientSock.recvfrom(1024)
            data = data[0].decode()
            print("flag3")
            print(data)
            try:
                print("flag4")
                stats = json.loads(data)
                print("flag5")
                break
            except:
                print("flag6")
                continue

        print("flag7")
        print("Stats Received.")

        totalBytesRecvd = stats["totalBytesRecvd"]
        numberOfPackets = stats["numberOfPackets"]

        goodput = totalBytesRecvd / durationOfTestInSeconds
        numberOfPackets = totalBytesRecvd / packetSizeInBytes
        packetReceptionRate = (numberOfPackets / totalPacketsSent) * 100

        print("Phone Uploaded to Peer: " + str(totalPacketsSent) + " packets")
        print("Goodput (raw): %s bytes" % (goodput))
        print("Goodput (Megabitsps): %s " % ((goodput * 8) / (1e6)))
        print("Goodput (MegaBytesps): %s " % ((goodput) / (1e6)))
        print("Number of Packets Received by Peer: " + str(numberOfPackets))
        print("Packet Reception Rate: " + str(packetReceptionRate) + "%")
        print('\n')

        x = input("Run again? (y/n)")
        if x == "n":
            print("Sending B: close, message and Server done (logout) message.")
            udpClientSock.sendto(str.encode("peer_close"), server_addr)
            udpClientSock.sendto(str.encode("done:a"), server_addr)
            udpClientSock.close()
            break
        elif x == "y":
            continue


# Device 2 should be logged into rendezvous server as: b
elif username == 'b':
    pktnumber = 0
    testRunning = False
    timeOutNotSet = True
    totalBytesRecvd = 0
    epochs = []
    STDBY = False
    while True:
        if not testRunning:
            data, client_addr = udpClientSock.recvfrom(65507)
            data = data.decode()
            if data == "peer_close":
                udpClientSock.close()
                break
            elif data == "keep-alive":
                continue
            elif data.split(":")[0] == "RPG":
                print("Initiating RPG...")
                packetSizeInBytes = int(data.split(":")[1])
                totalBytesRecvd = 0
                epochs = []
                udpClientSock.sendto(str.encode("OK"), client_addr)
                x = input("WARNING: Ensure b shows: \"Listening for packets...\", before running a.\nPress any key to continue.")
                print('Listening for packets...')
                testRunning = True
        else: # RPG Running
            try:
                data = udpClientSock.recvfrom(packetSizeInBytes)
                data = data[0].decode()
                if not STDBY and data == "keep-alive":
                    continue
                elif not STDBY and data == "peer_close":
                    udpClientSock.close()
                    break
                elif not STDBY and data == "peer_finish":
                    udpClientSock.settimeout(None)
                    timeOutNotSet = True
                    # Report bytes received
                    numberOfPackets = totalBytesRecvd / packetSizeInBytes

                    ojson = {
                        "totalBytesRecvd": totalBytesRecvd,
                        "numberOfPackets": numberOfPackets
                    }

                    udpClientSock.sendto(json.dumps(ojson).encode(), server_addr)
                    totalBytesRecvd = 0
                    pktnumber = 0
                    print("Listening for more measurements from A...")
                    state = True
                else:
                    # Clock receive time of arrival
                    totalBytesRecvd += len(data)
                    pktnumber += 1
                    if timeOutNotSet:
                        state = False
                        timeOutNotSet = False
                        udpClientSock.settimeout(5)
            except:
                print("Halted.")
                print("Listening for RPG message from A...")
                testRunning = False
                timeOutNotSet = True
                continue
