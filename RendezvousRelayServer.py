# RendezvousRelayServer.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app receives control messages from clients, establishes peering session and performs the request.
# a. RendezvousRelayServer:
#       Client A Sends: login, the RendezvousRelayServer will save the remote IP and port of the client A.
#       Client B sends: login, the RendezvousRelayServer will save the remote IP and port of the client B.
#       RendezvousRelayServer simply forwards the

# The purpose of this app is to measure the Layer 7 peer-to-peer delay from A<->RendezvousRelayServer<->B.

# The intended use is to run this app on a server.

# 1. Log into your server.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that RendezvousRelayServer ip and port are what you desire.
# 4. python3 RendezvousRelayServer.py

import socket
import sys
import signal
import json
import threading
import time

f = open('config.json',)
conf = json.load(f)
f.close()

peers = {
    'a': {
        'ip': '',
        'port': 0
    },
    'b': {
        'ip': '',
        'port': 0
    }
}

server_addr = (conf["rendezvous_relay_server"]["ip"], conf["rendezvous_relay_server"]["port"])
server_halt_addr = (conf["rendezvous_relay_server"]["ip"], conf["rendezvous_relay_server"]["halt_port"])

udpServerSock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpServerSock.bind(server_addr)
print("Peer Relay Server listening on " + server_addr[0] + ":" + str(server_addr[1]))

def signal_handler(sig, frame):
    udpServerSock.close()
    print('\n')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

keepthreadalive = True
def UDPkeepalive():
    global keepthreadalive
    while keepthreadalive:
        udpServerSock.sendto(str("keep-alive").encode(), (peers['a']['ip'], peers['a']['port']))
        udpServerSock.sendto(str("keep-alive").encode(), (peers['b']['ip'], peers['b']['port']))
        time.sleep(10)

th_keepalive = threading.Thread(name='UDPkeepalive',target=UDPkeepalive, args=())

peersNotified = False
while True:
    data, client_addr = udpServerSock.recvfrom(1024)
    data_ctrl_msg = data.decode().split(":")
    # User a is done.
    if data_ctrl_msg[0] == "done":
        udpServerSock.sendto(str("done").encode(), (peers['b']['ip'], peers['b']['port']))
        udpServerSock.sendto(str("done").encode(), (peers['a']['ip'], peers['b']['port']))
        keepthreadalive = False
        peersNotified = False
        peers = {
            'a': {
                'ip': '',
                'port': 0
            },
            'b': {
                'ip': '',
                'port': 0
            }
        }
        print('Logged all users out.')
        print("Peer Relay Server listening on " + server_addr[0] + ":" + str(server_addr[1]))
        continue

    # Begin Relay
    if peersNotified:
        if client_addr[0] == peers['a']['ip']:
            udpServerSock.sendto(data, (peers['b']['ip'], peers['b']['port']))
        elif client_addr[0] == peers['b']['ip']:
            udpServerSock.sendto(data, (peers['a']['ip'], peers['a']['port']))
            continue

    if data_ctrl_msg[0] == "login":
        if data_ctrl_msg[1] == "a":
            peers['a']['ip']=client_addr[0]
            peers['a']['port'] = client_addr[1]
            print(peers)
        elif data_ctrl_msg[1] == "b":
            peers['b']['ip'] = client_addr[0]
            peers['b']['port'] = client_addr[1]
            print(peers)

        udpServerSock.sendto(str("OK").encode(), client_addr)

    if (not peersNotified) and ((peers['b']['port'] > 0) and (peers['a']['port'] > 0)):
        udpServerSock.sendto(str("PEER").encode(), (peers['a']['ip'], peers['a']['port']))
        udpServerSock.sendto(str("PEER").encode(), (peers['b']['ip'], peers['b']['port']))
        peersNotified = True
        print("Peers Notified, echo service ready.")
        if not th_keepalive.isAlive():
            th_keepalive.start()
        keepthreadalive = True
