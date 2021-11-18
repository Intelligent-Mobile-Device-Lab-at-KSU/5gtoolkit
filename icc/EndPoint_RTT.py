# EndPoint_RTT.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app measures the Layer 7 delay to send a packet to the UDP EndPointServer.
# The purpose of this app is to measure the Layer 7 round trip time from this phone to the EndPointServer.

# The intended use is to run this app in Termux.
# Provide the number of times you would like to run this application.
# Statistics will be returned to you.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that end point server ip and port are correct.
# 4. python EndPoint_RTT.py <pktsize> <#ofpackets> [log] (log is optional, usually used for the Major Tests.

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

log = False
if len(sys.argv) == 4:
    pktsize_str = sys.argv[1]
    pktsize = int(pktsize_str)
    NumTimesToRun_str = sys.argv[2]
    NumTimesToRun = int(sys.argv[2])
    if sys.argv[3]=="log":
        log = True
elif len(sys.argv) == 3:
    pktsize_str = sys.argv[1]
    pktsize = int(pktsize_str)
    NumTimesToRun_str = sys.argv[2]
    NumTimesToRun = int(sys.argv[2])
else:
    print('Not enough arguments, \nusage: python EndPoint_RTT.py <pktsize> <#ofpackets> [log]')
    sys.exit(0)

pktnumber=0
delays = []
timestamps = []

server_addr = (conf["endpoint_server"]["ip"], conf["endpoint_server"]["port"])
logger_addr = (conf["logger_server"]["ip"], conf["logger_server"]["port"])

udpClientSock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def signal_handler(sig, frame):
    udpClientSock.close()
    print('\n')
    print("%d bytes sent and received!\n" % (pktnumber))
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
print('Sending ECHO Request to EndPointServer...')
udpClientSock.sendto(str.encode("ECHO:"+pktsize_str), server_addr)
respFromServer = udpClientSock.recvfrom(65507)
print('Server ready.')
print('Measurement in progress...')

while (pktnumber < NumTimesToRun):
    s = ''.join(random.choice(string.digits) for _ in range(pktsize))
    udpClientSock.sendto(s.encode(), server_addr)
    t = time.time()
    data = udpClientSock.recvfrom(65507)
    elapsed = time.time() - t
    delays.append(elapsed)
    timestamps.append(t)
    pktnumber += 1

udpClientSock.sendto(str.encode("ECHO:finish"), server_addr)
udpClientSock.close()

if len(delays) == 0:
    print("Divide by zero error. Maybe decrease the packet size? Try again.")
else:
    mu = sum(delays) / len(delays)
    variance = sum([((x - mu) ** 2) for x in delays]) / len(delays)
    stddev = variance ** 0.5
    multiplied_delays = [element * 1000 for element in delays]
    themin = min(multiplied_delays)
    themax = max(multiplied_delays)

    print("Completed %s measurements" % (pktnumber))
    print("Average: " + str(mu*1000) + "ms")
    print("Std.Dev: " + str(stddev*1000) + "ms")
    print("Min: " + str(themin) + "ms")
    print("Max: " + str(themax) + "ms")

    if log:
        print("===Logging PLEASE WAIT===")
        # Create data strings
        params_string = pktsize_str + "," + NumTimesToRun_str
        timestamp_string = ' '.join(str(e) for e in timestamps)
        delays_string = ' '.join(str(e) for e in delays)
        stats_string = "{},{},{},{},{}".format(str(mu * 1000), str(stddev * 1000), str(themin), str(themax), str(pktnumber))
        o = "{}\n{}\n{}\n{}\n".format(params_string, timestamps, delays_string, stats_string)

        # Create a TCP/IP socket
        tcpClientLoggerSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        print("connecting to LoggerServer...")
        tcpClientLoggerSock.connect(logger_addr)
        try:
            # Send Control Message:
            o = "NEW_LOG:"+sys.argv[0]
            print("Sending Ctrl Message: NEW_LOG")
            tcpClientLoggerSock.sendall(o)


            amount_received = 0
            while True:
                data = tcpClientLoggerSock.recv(4096)
                data = data.decode()
                print("received: " + data)
                if data == "BEGIN":
                    print("Sending Data...")
                    tcpClientLoggerSock.sendall(o)
                elif data == "DONE":
                    print("Data Logged.")
                    print("closing socket")
                    tcpClientLoggerSock.close()
                    break
        finally:
            print("Something went wrong...")
            print("closing socket")
            tcpClientLoggerSock.close()
