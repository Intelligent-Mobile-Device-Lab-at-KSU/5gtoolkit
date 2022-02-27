# HolePunchPeerGoodput.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app measures the Layer 7 one-way Goodput from this phone to the peer via a NAT hole-punch.
# A->NAT_Hole_Punch->B (measures Goodput) then B (sends stats back to A)->NAT_Hole_Punch->A

# The intended use is to run this app in Termux.
# Provide the number of times you would like to run this application.
# Statistics will be returned to you.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that NAT hole-punch server ip and port are correct.
# 4. python HolePunchPeerGoodput.py <a|b> <size of packets in bytes> <duration of measurement in seconds>
# 5. Example: python HolePunchPeerGoodput.py a 100 1, means: login as user 'a', send 100 byte packets for 1 second to 'b'
# 6. Example: python HolePunchPeerGoodput.py b 0 0, means: login as user 'b', measure Goodput on packets from 'a', send back results
# 7. A is always the sender. B is always the receiver.
# 8. Note: With two devices, one can choose one as A and the other as B, then switch roles.

import socket
import sys
import signal
import time
import json
import threading
import random
import string

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

f = open('config.json',)
conf = json.load(f)
f.close()

username = sys.argv[1] # can only be a or b
packetSizeInBytes_String = sys.argv[2]
packetSizeInBytes = int(packetSizeInBytes_String)
durationOfTestInSeconds_String = sys.argv[3]
durationOfTestInSeconds = int(durationOfTestInSeconds_String)

totalBytesSent = 0

server_addr = (conf["hole_punch_server"]["ip"], conf["hole_punch_server"]["port"])

udpClientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def signal_handler(sig, frame):
    if username=='a':
        # sending relay server to logout all users
        udpClientSock.sendto(str.encode("done:a"), server_addr)
    udpClientSock.close()
    print('\n')
    print("%d bytes echoed!\n" % (pktnumber))
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

tmp_str = "keep-alive:"+username
def udp_hole_keepalive():
    global username
    tmp_str = "keep-alive:"+username
    while True:
        udpClientSock.sendto(tmp_str.encode(), server_addr)
        time.sleep(10)

th_keepalive = threading.Thread(name='udp_hole_keepalive',target=udp_hole_keepalive, args=())

udpClientSock.sendto(str.encode("checkstatus:" + username), server_addr)

print("Logging In To Hole-Punch Server as username: " + username + "...")
respFromServer=''
while ("OK" not in respFromServer):
    udpClientSock.sendto(str.encode("login:" + username + ":" + local_ip + ":" + str(udpClientSock.getsockname()[1])), server_addr)
    respFromServer = udpClientSock.recvfrom(1024)
    respFromServer = respFromServer[0].decode()

respFromServer=''
print('Logged in as: '+username+ ", awaiting peer...")
while ("PEER" not in respFromServer):
    respFromServer = udpClientSock.recvfrom(1024)
    respFromServer = respFromServer[0].decode()

udpClientSock.sendto(str.encode("CONFIG_OK"), server_addr)
peer_addr = (respFromServer.split(":")[1], int(respFromServer.split(":")[2]))
peer_local_addr = (respFromServer.split(":")[3], int(respFromServer.split(":")[4]))
print(peer_addr)
print(peer_local_addr)

# th_keepalive.start()

respFromPeer = ''
print("Peer logged in.")
# Next we need to attempt to punch the hole
if username == 'a':
    print("Sending Hello...")
    udpClientSock.settimeout(1)
    while ("READY" not in respFromPeer):
        print("Sending Hello...")
        udpClientSock.sendto(tmp_str.encode(), server_addr)
        udpClientSock.sendto(str.encode("hello"), peer_addr)
        try:
            respFromPeer = udpClientSock.recvfrom(1024)
            respFromPeer = respFromPeer[0].decode()
        except:
            g=1
    udpClientSock.settimeout(None)

if username == 'b':
    print("Awaiting Peer Hello...")
    theaddr = ('',0)
    udpClientSock.settimeout(1)
    while ("hello" not in respFromPeer):
        udpClientSock.sendto(tmp_str.encode(), server_addr)
        udpClientSock.sendto(str.encode("0"), peer_addr)
        try:
            respFromPeer, theaddr = udpClientSock.recvfrom(1024)
            respFromPeer = respFromPeer.decode()
        except:
            g=1
    udpClientSock.settimeout(None)
    udpClientSock.sendto(str.encode("READY"), peer_addr)

    
udpClientSock.settimeout(5)
print("Emptying buffer, please wait...")
while (True):
    try:
        data = udpClientSock.recvfrom(packetSizeInBytes)
        message = data[0]
        address = data[1]
        print("Recevied from: %s, %s, %d" % (address[0], address[1],random.randint(0, 100)))
    except socket.timeout:
        print("Done.")
        udpClientSock.settimeout(None)
        break
print("Hole-Punch system ready.")
# Device 1 should be logged into hole-punch server as: a
if username == 'a':
    print('Sending Hole-Punch Peer Goodput (HP-PG) Request to Peer...')
    udpClientSock.sendto(str.encode("HP-PG:" + packetSizeInBytes_String), peer_addr)
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
            udpClientSock.sendto(s.encode(), peer_addr)
            totalPacketsSent += 1

        print("Done. Awaiting Stats From Peer...")
        stats = []
        udpClientSock.settimeout(5)
        while True:
            print("Attempting to fetch results")
            udpClientSock.sendto(str.encode("peer_finish"), peer_addr)
            try:
                data = udpClientSock.recvfrom(1024)
                data = data[0].decode()
                #print(data)
                stats = json.loads(data)
                break
            except:
                continue
        udpClientSock.settimeout(None)
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
            udpClientSock.sendto(str.encode("peer_close"), peer_addr)
            udpClientSock.sendto(str.encode("done:a"), server_addr)
            udpClientSock.close()
            break
        elif x == "y":
            udpClientSock.settimeout(5)
            print("Emptying buffer, please wait...")
            while (True):
                try:
                    data = udpClientSock.recvfrom(packetSizeInBytes)
                    message = data[0]
                    address = data[1]
                    print("Recevied from: %s, %s, %d" % (address[0], address[1],random.randint(0, 100)))
                except socket.timeout:
                    print("Done.")
                    udpClientSock.settimeout(None)
                    break
            continue

# Device 2 should be logged into relay server as: b
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
            elif data.split(":")[0] == "HP-PG":
                print("Initiating HP-PG...")
                packetSizeInBytes = int(data.split(":")[1])
                totalBytesRecvd = 0
                epochs = []
                udpClientSock.sendto(str.encode("OK"), client_addr)
                x = input(
                    "WARNING: Ensure b shows: \"Listening for packets...\", before running a.\nPress any key to continue.")
                print('Listening for packets...')
                testRunning = True
        else:  # HP-PG Running
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

                    udpClientSock.sendto(json.dumps(ojson).encode(), peer_addr)
                    totalBytesRecvd = 0
                    pktnumber = 0
                    print("Listening for more measurements from A...")
                    state = True
                else:
                    # Accumulate the # of Bytes received.
                    totalBytesRecvd += len(data)
                    pktnumber += 1
                    if timeOutNotSet:
                        state = False
                        timeOutNotSet = False
                        udpClientSock.settimeout(5)
            except:
                print("Halted.")
                print("Listening for HP-PG message from A...")
                testRunning = False
                timeOutNotSet = True
                continue
