import socket
import threading
import sys
import signal
import time

tx=0
rx=0
server_addr = (sys.argv[1], int(sys.argv[2]))
print(sys.argv[1])
udpSerSock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def rxMsg():
    global rx
    while True:
        data, addr = udpSerSock.recvfrom(65000)
        rx+=len(data)
        time.sleep(.1)

try:
   rev_thread = threading.Thread(target = rxMsg)
   rev_thread.setDaemon(True)
   rev_thread.start()
except:
   print("Error: unable to start thread")

def signal_handler(sig, frame):
    udpSerSock.close()
    print('\n')
    print("%d bytes sent!\n" % (tx))
    print("%d bytes rx!\n" % (rx))
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if (int(sys.argv[2])==0):
    print('Sounding...')
    while True:
        udpSerSock.sendto(str.encode("0"), server_addr)
        tx+=len(str.encode("0"))
        time.sleep(.1)
else:
    stime = time.time();
    while (time.time()-stime) <=10:
        udpSerSock.sendto(str.encode("0"), server_addr)
        tx+=len(str.encode("0"))
        #time.sleep(.1)
    o = "I Tx %d Bytes in 10 seconds!" % (tx)
    print(o)
