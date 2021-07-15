import socket
import threading
import time
from datetime import datetime
import time

from losantmqtt import Device


cmd_state = 0

# device_id = "60df807fdce6c40006fc4fc7"  # nat-punch-device-1
device_id = "60ebfdecd77a3c00079b55b0"  # nat-punch-device-2
self_ip = ""
self_port = ""
host_name = "client2"
validation_msg = ""
epocharray = [0,0,0,0,0,0,0,0,0,0]
counter=0
def on_command(device, command):
    print("Command received.")
    print(command["name"])
    print(command["payload"])


server_addr = ("143.244.159.219", 27000)
udpSerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


response = {}


def heartbeat():
    tmp_str = ("%d|%s|%s" % (9, "keep ", "live")).encode()
    while True:
        udpSerSock.sendto(tmp_str, server_addr)
        time.sleep(10)


def revMsg():
    global peer_ip, peer_port, cmd_state, counter, epocharray

    print(f"{datetime.now()} - Starting Receive Thread.\n")
    while True:
        data, addr = udpSerSock.recvfrom(1024)
        epoch = time.time()
        data = data.decode()

        try:
            (msg_type, msg_arg1, msg_arg2) = str(data).split("|")
            msg_type = int(msg_type)
        except:
            print(f"{datetime.now()} - error msg! {str(data)}")
            continue

        if msg_type == 9:  # heart beat
            # print(f"msg 9 received, {msg_arg1} {msg_arg2}")
            continue

        elif msg_type == 0:  # successfully connected to server
            self_ip = msg_arg1
            self_port = msg_arg2
            print(f"{datetime.now()} - login success. {self_ip} {self_port} ]")
            cmd_state = 2  # look for peer

        elif msg_type == 1:  # print out list of connected IP: PORT
            print(f"{datetime.now()} - online hosts:\n%s" % (msg_arg1))

        elif msg_type == 2:
            print(f"{datetime.now()} - peer online")
            peer_ip = msg_arg1
            peer_port = msg_arg2
            get_peer_counter = 0
            cmd_state = 3  # validate connection

        elif msg_type == 3:
            print(f"{datetime.now()} - peer offline")
            get_peer_counter += 1
            cmd_state = 2  # look for client 2

        elif msg_type == 4:
            print(f"{datetime.now()} - respond peer: [{msg_arg1}]  [{msg_arg2}]")
            peer_ip = msg_arg1
            peer_port = msg_arg2
            udpSerSock.sendto(
                ("%d|%s|%s" % (9, "hello", " ")).encode(), (msg_arg1, int(msg_arg2))
            )

        elif msg_type == 5:
            print(f"{datetime.now()} - peer msg received:{msg_arg1}")
            udpSerSock.sendto(
                ("%d|%s|%s" % (8, msg_arg1, " ")).encode(), (peer_ip, int(peer_port))
            )

        elif msg_type == 6:
            epocharray[counter]=epoch
            counter+=1
            print(f"{datetime.now()} - peer msg:", msg_arg1, msg_arg2)
            udpSerSock.sendto(
                ("%d|%s|%s" % (7, msg_arg1, msg_arg2)).encode(),
                (peer_ip, int(peer_port)),
            )
        elif msg_type == 13:
            indy=0
            mysum=0
            while indy<=8:
                mysum+=(epocharray[indy+1]-epocharray[indy])
            jitter=mysum/9
            udpSerSock.sendto(
                ("%d|%s|%s" % (13, str(jitter), str(jitter))).encode(),
                (peer_ip, int(peer_port)),
            )
        elif msg_type == 7:
            print(
                f"{datetime.now()} [ping received]:  { (time.time() - float(msg_arg1)) * 1000}"
            )
            device.loop()
            if device.is_connected():
                device.send_state(
                    {
                        "epoch": time.time(),
                        "resp_time": (time.time() - float(msg_arg1)) * 1000,
                    }
                )
            else:
                print(f"{datetime.now()} - error Type! ", str(data))
        elif msg_type == 8:
            if validation_msg == msg_arg1:
                print(f"{datetime.now()} - valid msg {msg_arg1} recevied")
            else:
                print(
                    f"{datetime.now()} - Invalid msg received {msg_arg1} should be {validation_msg} "
                )


try:

    heat_thread = threading.Thread(target=heartbeat)
    heat_thread.setDaemon(True)
    heat_thread.start()

    rev_thread = threading.Thread(target=revMsg)
    rev_thread.setDaemon(True)
    rev_thread.start()


except:
    print("Error: unable to start thread")

# ========================
host_name = "Noname"
# Execute the 0, 1, 2, 3 commands in turn to complete the p2p connection and chat directly
while True:
    # comd = input("Commend[0,1,2,3,4,5,6]>>")
    # # query online host
    # strip_cmd = str(comd).strip()
    strip_cmd = str(cmd_state)
    if strip_cmd == "0":
        host_name = "client2"
        udpSerSock.sendto(
            ("%d|%s|%s" % (0, str(host_name).strip(), " ")).encode(), server_addr
        )
    elif strip_cmd == "1":
        print(f"{datetime.now()} - get online host...")
        udpSerSock.sendto(("%d|%s|%s" % (1, " ", " ")).encode(), server_addr)

    elif strip_cmd == "2":
        print("Waiting...Type 'exit'")
        msg = input("cmd>>")
        if msg == "exit":
            break
    time.sleep(1)
udpSerSock.close()
#{"mode":"full","isActive":false}
