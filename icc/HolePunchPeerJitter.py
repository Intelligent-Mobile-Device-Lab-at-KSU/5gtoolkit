# HolePunchPeerJitter.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app measures the Layer 7 one-way jitter from this phone to the peer via a NAT hole-punch.
# A->NAT_Hole_Punch->B (measures jitter) then B (sends stats back to A)->NAT_Hole_Punch->A

# The intended use is to run this app in Termux.
# Provide the number of times you would like to run this application.
# Statistics will be returned to you.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that RendezvousRelayServer server ip and port are correct.
# 4. python HolePunchPeerJitter.py <a|b> <size of packets in bytes> <duration of measurement in seconds>
# 5. Example: python HolePunchPeerJitter.py a 100 1, means: login as user 'a', send 100 byte packets for 1 second to 'b'
# 6. Example: python HolePunchPeerJitter.py b 0 0, means: login as user 'b', measure jitter on packets from 'a', send back results
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

print("Hole-Punch system ready.")
# Device 1 should be logged into hole-punch server as: a
if username == 'a':
    print('Sending Relay Peer Jitter (HP-PJ) Request to Peer...')
    udpClientSock.sendto(str.encode("HP-PJ:" + packetSizeInBytes_String), peer_addr)
    while True:
        respFromPeer = udpClientSock.recvfrom(65507)
        respFromPeer = respFromPeer[0].decode()
        if respFromPeer == "keep-alive":
            continue
        elif respFromPeer == "OK":
            print('Peer ready.')
            print("Ensure b displays \"Listening for packets...\" then when ready...")
            break

    x=input("Press any key to begin jitter test through NAT Hole-Punch...")
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
        while True:
            udpClientSock.sendto(str.encode("peer_finish"), peer_addr)
            data = udpClientSock.recvfrom(1024)
            data = data[0].decode()
            try:
                stats = json.loads(data)
                break
            except:
                continue

        if stats["error"]:
            print("Divide by zero error at the Server. Maybe decrease the packet size? Try again.")
            print('\n')
            x = input(
                "Run again with new packet size (type n to end / k to keep same size: " + packetSizeInBytes_String + "): ")
            if x == "n":
                print("Sending B: stop, message.")
                udpClientSock.sendto(str.encode("stop"), peer_addr)
                udpClientSock.close()
                break
            if x == "k":
                continue
            else:
                packetSizeInBytes_String = x
                packetSizeInBytes = int(packetSizeInBytes_String)
                continue
        else:
            print("Stats Received.")
            print("Phone attempted to send %s packets" % (totalPacketsSent))
            print("Jitter average: " + str(stats["avg"]) + "ms")
            print("Jitter std.dev: " + str(stats["stddev"]) + "ms")
            print("Jitter min: " + str(stats["min"]) + "ms")
            print("Jitter max: " + str(stats["max"]) + "ms")
            print('\n')
            x = input("Run again? (y/n)")
            if x == "n":
                print("Sending B: close, message and Server done (logout) message.")
                udpClientSock.sendto(str.encode("peer_close"), peer_addr)
                udpClientSock.sendto(str.encode("done:a"), server_addr)
                udpClientSock.close()
                break
            elif x == "y":
                continue

# Device 2 should be logged into relay server as: b
elif username == 'b':
    pktnumber = 0
    HPPJrunning = False
    timeOutNotSet = True
    totalBytesRecvd = 0
    epochs = []
    STDBY = False
    while True:
        if not HPPJrunning:
            data, client_addr = udpClientSock.recvfrom(65507)
            data = data.decode()
            if data == "peer_close":
                udpClientSock.close()
                break
            elif data == "keep-alive":
                continue
            elif data.split(":")[0] == "HP-PJ":
                print("Initiating HP-PJ...")
                packetSizeInBytes = int(data.split(":")[1])
                totalBytesRecvd = 0
                epochs = []
                udpClientSock.sendto(str.encode("OK"), peer_addr)
                x = input(
                    "WARNING: Ensure b shows: \"Listening for packets...\", before running a.\nPress any key to continue.")
                print('Listening for packets...')
                HPPJrunning = True
        else:  # HP-PJ running
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
                    udpClientSock.sendto(json.dumps(ojson).encode(), peer_addr)
                    totalBytesRecvd = 0
                    epochs = []
                    pktnumber = 0
                    print("Listening for more measurements from A...")
                    state = True
                else:
                    # Clock receive time of arrival
                    epochs.append(time.time())
                    pktnumber += 1
                    if timeOutNotSet:
                        state = False
                        timeOutNotSet = False
                        udpClientSock.settimeout(5)
            except:
                print("Halted.")
                print("Listening for HP-PJ message from A...")
                HPPJrunning = False
                timeOutNotSet = True
                continue
