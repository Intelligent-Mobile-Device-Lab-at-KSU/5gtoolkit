# HolePunchPeerRTT.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app measures the Layer 7 delay to send the character '0' to a peer via a NAT hole-punch.
# The purpose of this app is to measure the Layer 7 round trip time from this phone to the other phone via a NAT hole-punch.
# A->NAT_Hole_Punch->B->NAT_Hole_Punch->A

# The intended use is to run this app in Termux.
# Provide the number of times you would like to run this application.
# Statistics will be returned to you.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that RendezvousRelayServer server ip and port are correct.
# 4. python HolePunchPeerRTT.py <a|b> <pktsize> <#ofpackets>
# 5. Example: python HolePunchPeerRTT.py a 1 10, means: login as user A, send 1 byte 10 times to B
# 6. Example: python HolePunchPeerRTT.py b, means: login as user B, get ten packets of size one byte from A

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
        data = udpClientSock.recvfrom(pktsize)
        message = data[0]
        address = data[1]
        print("Recevied from: %s, %s, %d" % (address[0], address[1],random.randint(0, 100)))
    except socket.timeout:
        print("Done.")
        udpClientSock.settimeout(None)
        break
print("Hole-Punch system ready.")
# Device 1 should be logged into relay server as: a
if username == 'a':
    print("Ensure b displays \"Listening for packets...\" then when ready...")
    x=input("Press any key to begin delay test through NAT Hole-Punch...")
    while True:
        print('Sending Packets')
        pktnumber = 0
        delays = []
        s = ''.join(random.choice(string.digits) for _ in range(pktsize))
        s = "GET /search?q=test HTTP/2\nHost: www.bing.com\nUser-Agent: curl/7.54.0\nAccept: */"
        while (pktnumber < NumTimesToRun):
            udpClientSock.sendto(s.encode(), peer_addr)
            t = time.time()
            data = udpClientSock.recvfrom(pktsize)
            elapsed=time.time()-t
            delays.append(elapsed)
            pktnumber += 1
        #message = data[0]
        #address = data[1]
        #print("Recevied from: %s, %s, %0.5f" % (address[0], address[1],elapsed))
        #if data[0].decode()=="keep-alive":
        #    continue
        #if elapsed==0.0:
        #    udpClientSock.sendto(s.encode(), peer_addr)
        #    t = time.time()
        #    continue
        #delays.append(elapsed)
        #pktnumber += 1

        if len(delays) == 0:
            print("Divide by zero error. Maybe decrease the packet size? Try again.")
        else:
            print(delays)
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
                udpClientSock.sendto(str.encode("peer_close"), peer_addr)
                udpClientSock.close()
                break
            elif x=="y":
                continue

# Device 2 should be logged into relay server as: b
elif username == 'b':
    print("WARNING: Ensure b shows: \"Listening for packets...\", before running a")
    x=input("Press any key to receiving packets...")
    print('Listening for packets...')
    while True:
        data, client_addr = udpClientSock.recvfrom(pktsize)
        #message = data
        #address = client_addr
        #print("Recevied from: %s, %s" % (address[0], address[1]))
        if data.decode() == "peer_close":
            udpClientSock.close()
            break
        elif data.decode() == "keep-alive":
            continue
        else:
            udpClientSock.sendto(data, peer_addr)
            pktnumber += 1
