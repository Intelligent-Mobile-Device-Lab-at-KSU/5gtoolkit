# RelayPeerLatency.py
# Billy Kihei (c) 2022
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing public 5G networks.

# This app measures the Layer 7 one-way delay to send the character '0' or '1' to a peer via a RendezvousRelayServer.
# The purpose of this app is to measure the Layer 7 one-way delay from this phone to the other phone via RendezvousRelayServer.
# A->RendezvousRelayServer->B->RendezvousRelayServer->A, 
# this is not an echo or RTT measurement. You will need to have a common clock observering device to be able to measure the one-way delay.

# The intended use is to run this app in Termux.
# Provide the number of times you would like to run this application.
# Statistics will be returned to you.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that RendezvousRelayServer server ip and port are correct.
# 4. python RelayPeerLatency.py <a|b> <pktsize> <#ofpackets>
# 5. Example: python RelayPeerLatency.py a 1 100, means: login as user A, send 1 byte 100 times to B
# 6. Example: python RelayPeerLatency.py b 1 100, means: login as user B, get one hundred packets of size one byte from A

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

if len(sys.argv) == 4:
    username = sys.argv[1] # can only be a or b
    pktsize = int(sys.argv[2])
    NumTimesToRun = int(sys.argv[3])
elif sys.argv[1]=='a':
    print('Not enough arguments for user A, \nusage: python HolePunchPeerRTT.py <a|b> <pktsize> <#ofpackets>')
    sys.exit(0)
else:
    username = sys.argv[1] # you are B

pktnumber = 0

server_addr = (conf["rendezvous_relay_server"]["ip"], conf["rendezvous_relay_server"]["port"])

udpClientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 14400  # The port used by the TCP server
tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_client_socket.connect((HOST, PORT))

def signal_handler(sig, frame):
    if username=='a':
        # sending relay server to logout all users
        udpClientSock.sendto(str.encode("done:a"), server_addr)
    udpClientSock.close()
    print('\n')
    print("%d bytes echoed!\n" % (pktnumber))
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

udpClientSock.settimeout(5)
print("Emptying buffer, please wait...")
while (True):
    try:
        data = udpClientSock.recvfrom(pktsize)
        message = data[0]
        address = data[1]
        print("Recevied from: %s, %s, %d" % (address[0], address[1],random.randint(0, 100)))
    except socket.timeout:
        print("Done.")
        udpClientSock.settimeout(None)
        break
print("Peer found. Echo system ready.")

# Device 1 should be logged into relay server as: a
if username == 'a':
    print("Ensure b displays \"Listening for packets...\" then when ready...")
    x=input("The press any key to begin delay test through Rendezvous Relay Server...")
    while True:
        print('Sending Packets')
        pktnumber = 0
        while (pktnumber < NumTimesToRun):
            s = ''.join(random.choice(string.digits) for _ in range(pktsize))
            udpClientSock.sendto(s.encode(), server_addr)
            ss = '1'
            tcp_client_socket.sendall(ss.encode())
            print("Sent Pkt")
            time.sleep(1)
            s='0'
            udpClientSock.sendto(s.encode(), server_addr)
            ss = '0'
            tcp_client_socket.sendall(ss.encode())
            time.sleep(1)
            pktnumber += 1
            continue

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
            if x == "n":
                print("Sending B: closed, message.")
                udpClientSock.sendto(str.encode("peer_close"), server_addr)
                udpClientSock.close()
                break
            elif x=="y":
                udpClientSock.settimeout(5)
                print("Emptying buffer, please wait...")
                while (True):
                    try:
                        data = udpClientSock.recvfrom(pktsize)
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
    print("WARNING: Ensure b shows: \"Listening for packets...\", before running a")
    x=input("Press any key to receiving packets...")
    print('Listening for packets...')
    while True:
        data, client_addr = udpClientSock.recvfrom(pktsize)
        if data.decode() == "peer_close":
            udpClientSock.close()
            break
        elif (data.decode() == "keep-alive") or ("keep-alive" in data.decode()):
            continue
        else:
            if data.decode()=='0':
               tcp_client_socket.sendall(data)
               print('0')
            else:
              tcp_client_socket.sendall("1".encode())
              print('1')
            pktnumber += 1
