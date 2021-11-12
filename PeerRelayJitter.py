# PeerRelayJitter.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app measures the Layer 7 one-way jitter from this phone to the peer via a RendezvousRelayServer.
# A->RendezvousRelayServer->B (measures jitter) then B (sends stats back to A)->RendezvousRelayServer->A

# The intended use is to run this app in Termux.
# Provide the number of times you would like to run this application.
# Statistics will be returned to you.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that RendezvousRelayServer server ip and port are correct.
# 4. python PeerRelayJitter.py <a|b> <size of packets in bytes> <duration of measurement in seconds>
# 5. Example: python PeerRelayJitter.py a 100 1, means: login as user 'a', send 100 byte packets for 1 second to 'b'
# 6. Example: python PeerRelayJitter.py b 0 0, means: login as user 'b', receive packets from 'a', send back results
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
    udpClientSock.close()
    print('\n')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

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

print("Peer found. Peer Jitter system ready.")

# Device 1 should be logged into rendezvous server as: a
if username == 'a':
    print('Sending Relay Peer Jitter (RPJ) Request to Peer...')
    udpClientSock.sendto(str.encode("RPJ:" + packetSizeInBytes_String), server_addr)
    while True:
        respFromPeer = udpClientSock.recvfrom(65507)
        respFromPeer = respFromPeer[0].decode()
        if respFromPeer=="keep-alive":
            continue
        elif respFromPeer=="OK":
            print('Peer ready.')
            print("Ensure b displays \"Listening for packets...\" then when ready...")
            break

    x = input("Press any key to begin peer jitter test through Rendezvous Relay Server...")
    while True:
        print('Measurement in progress...')
        totalPacketsSent = 0
        t = time.time()
        while (time.time() - t) <= durationOfTestInSeconds:
            s = ''.join(random.choice(string.digits) for _ in range(packetSizeInBytes))
            udpClientSock.sendto(s.encode(), server_addr)
            totalPacketsSent += 1

        print("Done. Awaiting Stats From Peer...")
        udpClientSock.sendto(str.encode("done"), server_addr)
        respFromServer = udpClientSock.recvfrom(1024)
        stats = json.loads(respFromServer[0].decode())

        if stats["error"]:
            print("Divide by zero error at the Server. Maybe decrease the packet size? Try again.")
            print('\n')
            x = input("Run again with new packet size (type n to end): ")
            if x == "n":
                print("Sending B: done, message.")
                udpClientSock.sendto(str.encode("done:a"), server_addr)
                udpClientSock.close()
                break
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
                print("Sending B: done, message.")
                udpClientSock.sendto(str.encode("done:a"), server_addr)
                udpClientSock.close()
                break
            elif x == "y":
                continue


# Device 2 should be logged into rendezvous server as: b
elif username == 'b':
    pktnumber = 0
    RPJrunning = False
    timeOutNotSet = True
    while True:
        if not RPJrunning:
            data, client_addr = udpClientSock.recvfrom(65507)
            data = data.decode()
            if data == "stop":
                udpClientSock.close()
                break
            elif data == "keep-alive":
                continue
            elif data.split(":")[0] == "RPJ":
                print("Initiating RPJ...")
                packetSizeInBytes = int(data.split(":")[1])
                totalBytesRecvd = 0
                epochs = []
                udpClientSock.sendto(str.encode("OK"), client_addr)
                x = input("WARNING: Ensure b shows: \"Listening for packets...\", before running a.\nPress any key to continue.")
                print('Listening for packets...')
                RPJrunning = True
        else: # RPJ running
            try:
                data = udpClientSock.recvfrom(packetSizeInBytes)
                if timeOutNotSet:
                    timeOutNotSet = False
                    udpClientSock.settimeout(5)
                data = data[0].decode()
                if data == "keep-alive":
                    continue
                elif data == "done":
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
                    udpClientSock.sendto(json.dumps(ojson).encode(), server_addr)
                    totalBytesRecvd = 0
                    epochs = []
                else:
                    epochs.append(time.time())
                    pktnumber += 1
            except:
                print("Halted.")
                print("Listening for RPJ message from A...")
                RPJrunning = False
                timeOutNotSet = True
                continue
