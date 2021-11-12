# RelayPeerEcho.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app measures the Layer 7 delay to send the character '0' to a peer via a RendezvousRelayServer.
# The purpose of this app is to measure the Layer 7 round trip time from this phone to the other phone via RendezvousRelayServer.
# A->RendezvousRelayServer->B->RendezvousRelayServer->A

# The intended use is to run this app in Termux.
# Provide the number of times you would like to run this application.
# Statistics will be returned to you.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that echo server ip and port are correct.
# 4. python RelayPeerEcho.py <a|b> <number of measurements>
# 5. Example: python RelayPeerEcho.py a 10, means: login as user 'a', get 10 echoes from 'b'
# 6. Example: python RelayPeerEcho.py b 10, means: login as user 'b', get 10 echoes from 'a'

import socket
import sys
import signal
import time
import json
f = open('config.json',)
conf = json.load(f)
f.close()

username = sys.argv[1] # can only be a or b
NumTimesToRun = int(sys.argv[2])

pktnumber = 0

server_addr = (conf["rendezvous_relay_server"]["ip"], conf["rendezvous_relay_server"]["port"])

udpClientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def signal_handler(sig, frame):
    if username=='a':
        udpClientSock.sendto(str.encode("done:a"), server_addr)
    udpClientSock.close()
    print('\n')
    print("%d bytes echoed!\n" % (pktnumber))
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


print('Logging In To Rendezvous Relay Server...')
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

print("Peer found. Echo system ready")

if username == 'a':
    x=input("Press any key to begin echo...")
    while True:
        print('Sending Packets')
        pktnumber = 0
        delays = []
        while (pktnumber < NumTimesToRun):
            udpClientSock.sendto(str.encode("0"), server_addr)
            t = time.time()
            data = udpClientSock.recvfrom(1024)
            if data[0].decode()=="keep-alive":
                continue
            elapsed = time.time() - t
            delays.append(elapsed)
            pktnumber += 1

        if len(delays) == 0:
            print("Divide by zero error. Maybe decrease the packet size? Try again.")
        else:
            mu = sum(delays) / len(delays)
            variance = sum([((x - mu) ** 2) for x in delays]) / len(delays)
            stddev = variance ** 0.5
            multiplied_delays = [element * 1000 for element in delays]
            themin = min(multiplied_delays)
            themax = max(multiplied_delays)

            print("Peer Relay completed %s measurements" % (pktnumber))
            print("Average: " + str(mu*1000) + "ms")
            print("Std.Dev: " + str(stddev*1000) + "ms")
            print("Min: " + str(themin) + "ms")
            print("Max: " + str(themax) + "ms")
            print('\n')
            x=input("Run again? (y/n)")
            if x=="n":
                udpClientSock.sendto(str.encode("done:a"), server_addr)
                udpClientSock.close()
                break
            elif x=="y":
                continue

elif username == 'b':
    x=input("Press any key to receiving packets...")
    print('Listening for packets...')
    while True:
        data, client_addr = udpClientSock.recvfrom(1024)
        if data.decode() == "done":
            udpClientSock.close()
            break
        elif data.decode() == "keep-alive":
            continue
        else:
            udpClientSock.sendto(data, client_addr)
            pktnumber += 1
