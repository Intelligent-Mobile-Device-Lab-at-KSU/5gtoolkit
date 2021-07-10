import socket
import threading
import time
import sys
import signal

server_addr = (sys.argv[2], int(sys.argv[3]))
udpSerSock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

peer_ip=''
peer_port=''
ttime=0
tc = 0 # tx count
rc=0 # rx count

def heartbeat():
    while True:
        udpSerSock.sendto(str.encode('%d|%s|%s' % (9, "keep ", "live")), server_addr)
        time.sleep(1)

def revMsg():
    global peer_ip,peer_port,rc
    print(" start rev:")
    while True:
        data, addr = udpSerSock.recvfrom(65000)
        try:
            (msg_type,msg_arg1,msg_arg2)=str(data.decode("utf-8")).split('|')
        except:
            print('[error msg!]', str(data))
            continue
        if int(msg_type)==9:
            continue
        elif int(msg_type)==0:
            print('[login success: %s]' % (str(data)))
        elif int(msg_type)==1:
            print("online hosts:\n%s"% (msg_arg1))
        elif int(msg_type)==2:
            print('[peer online]')
            peer_ip=msg_arg1
            peer_port=msg_arg2
        elif int(msg_type)==3:
            print('[peer offline]')
        elif int(msg_type)==4:
            print('[respond peer]')
            udpSerSock.sendto(str.encode('%d|%s|%s' % (9,"hello"," ")), (msg_arg1,int(msg_arg2)))
        elif int(msg_type)==5:
            rc+=1
            #print('[peer msg]:%s'% msg_arg1)
        else:
            print('[error Type!]', str(data))

try:
   rev_thread = threading.Thread(target = revMsg)
   rev_thread.setDaemon(True)
   rev_thread.start()

   heat_thread=threading.Thread(target = heartbeat)
   heat_thread.setDaemon(True)
   heat_thread.start()
except:
   print("Error: unable to start thread")

# ========================
host_name="Noname"
login=True
def signal_handler(sig, frame):
    global host_name, ttime
    udpSerSock.close()
    if sys.argv[1]=="tx":
        print('\n')
        print('\n')
        print(5*tc)
        print('Bytes sent!\n')
    else:
        print('\n')
        print('\n')
        print(5*rc)
        print('Bytes received!\n')
        endt = time.time()    
        elapsed = (endt - ttime) - 1
        print(elapsed)
        print((5*rc)/(1e6*elapsed))
        print('MBps\n')
    sys.exit(0)
    ######
# Execute the 0, 1, 2, 3 commands in turn to complete the p2p connection and chat directly
signal.signal(signal.SIGINT, signal_handler)

while True:
    comd = input("Commend[0,1,2,3]>>")
    # query online host
    if str(comd).strip()=='0':
        host_name = input("hostname>>")
        udpSerSock.sendto(str.encode('%d|%s|%s' % (0,str(host_name).strip()," ")), server_addr)
    elif str(comd).strip()=='1':
        print("get online host...")
        udpSerSock.sendto(str.encode('%d|%s|%s' % (1," "," ")), server_addr)
    elif str(comd).strip()=='2':
        peer_name = input("peer_name>>")
        print("get peer ip...")
        udpSerSock.sendto(str.encode('%d|%s|%s' % (2,str(peer_name).strip()," ")), server_addr)
        break
                 
ttime = time.time()
if sys.argv[1]=="tx":
    time.sleep(1)
    #comd = input("Ready to begin?>>")
    while True:
        udpSerSock.sendto(str.encode('%d|%s|%s' % (5,str('0')," ")), (peer_ip,int(peer_port)))
        tc+=1
else:
    while True:
        time.sleep(100)