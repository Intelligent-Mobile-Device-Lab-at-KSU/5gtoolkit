# HolePunchLatency.py
# Billy Kihei (c) 2022
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app measures the one-way Layer 7 delay to send bytes to a peer via a NAT hole-punch.
# The purpose of this app is to measure the Layer 7 one-way delay (end-to-end) from this phone to the other phone via a NAT hole-punch.
# A->NAT_Hole_Punch->B, this is not an echo or RTT measurement. You will need to have a common clock observering device to be able to measure the one-way delay.

# The intended use is to run this app in Termux. This is not a standalone app.
# Provide the number of times you would like to run this application.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that HolePunchRendezvousServer server ip and port are correct.
# 4. python HolePunchLatency.py <a|b> <pktsize> <#ofpackets>
# 5. Example: python HolePunchLatency.py a 1 10, means: login as user A, send 1 byte 10 times to B
# 6. Example: python HolePunchLatency.py b, means: login as user B, get ten packets of size one byte from A

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
    print('Not enough arguments for user A, \nusage: python HolePunchLatency.py <a|b> <pktsize> <#ofpackets>')
    sys.exit(0)
else:
    username = sys.argv[1] # you are B


pktnumber = 0

server_addr = (conf["hole_punch_server"]["ip"], conf["hole_punch_server"]["port"])

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
        while (pktnumber < NumTimesToRun):
            #s = ''.join(random.choice(string.digits) for _ in range(pktsize))
            if (pktnumber % 2) == 0:
                s="0"
            else:
                s="1"
            udpClientSock.sendto(s.encode(), peer_addr)
            tcp_client_socket.sendall(s.encode())
            print(s.decode())
            pktnumber += 1
            continue

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

            print("Hole-Punch Peer completed %s measurements" % (pktnumber))
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
    print("WARNING: Ensure you have b connected to an observation system. This is not a stand-alone app!")
    print("WARNING: Ensure b shows: \"Listening for packets...\", before running a")
    x=input("Press any key to receiving packets...")
    print('Listening for packets...')
    while True:
        data, client_addr = udpClientSock.recvfrom(pktsize)
        if data.decode() == "peer_close":
            udpClientSock.close()
            break
        elif data.decode() == "keep-alive":
            continue
        else:
            #pkt rcved
            tcp_client_socket.sendall(data)
            print(data.decode())
            pktnumber += 1
