import socket
import threading
import time
from datetime import datetime
import time
import sys

from losantmqtt import Device

cmd_state = 0
device_id = "60ebfdddbe3fc900069df64a"  # nat-punch-device-1
# device_id = "60ebfdecd77a3c00079b55b0"  # nat-punch-device-2

peer_counter_limit = 50  # give up after trying to connect with peer
sleep_time = 1  # number of seconds between tries

get_peer_counter = 0
tmpTime = 0

def on_command(device, command):
    print("Command received.")
    print(command["name"])
    print(command["payload"])


server_addr = ("143.244.159.219", 27000)
# server_addr = ("192.168.1.70", 6000)
udpSerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# udpSerSock.bind(server_addr)
Clinet_Name = "clinet_A"
self_ip = ""
self_port = ""
host_name = "client1"
peer_name = "client2"
validation_msg = ""
counter=0
endprogram=False

def heartbeat():
    tmp_str = ("%d|%s|%s" % (9, "keep ", "live")).encode()
    while True:
        udpSerSock.sendto(tmp_str, server_addr)
        time.sleep(10)


def revMsg():
    global peer_ip, peer_port, cmd_state, get_peer_counter, counter, endprogram

    # Construct device
    device = Device(
        device_id,
        "236e0f54-4074-4850-b5a0-20052c8a9601",
        "f8bf01ed21898b61a597545dfe9de4beb6c374dd0c91f2bba196298cdfc2352a",
    )

    # Listen for commands.
    device.add_event_observer("command", on_command)

    # Connect to Losant.
    device.connect(blocking=False)
    # scp -P 8022 client.py u0_a385@192.168.1.176:~/.
    # scp -P 8022 client.py u0_a212@192.168.1.168:~/.

    print("Starting Receive Thread:")
    while True:
        data, addr = udpSerSock.recvfrom(1024)
        data = data.decode()
        try:
            (msg_type, msg_arg1, msg_arg2) = str(data).split("|")
            msg_type = int(msg_type)
        except:
            print(f"{datetime.now()} - error msg! ", str(data))
            continue
        if msg_type == 9:
            # print(f"msg 9 received, {msg_arg1} {msg_arg2}")
            continue

        elif msg_type == 0:
            self_ip = msg_arg1
            self_port = msg_arg2
            print(f"{datetime.now()} - login success: {self_ip} {self_port}")
            cmd_state = 2  # look for peer

        elif msg_type == 1:
            print(f"{datetime.now()} - online hosts: {msg_arg1}")

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
            print(f"{datetime.now()} - respond peer [{msg_arg1}]  [{msg_arg2}]")
            peer_ip = msg_arg1
            peer_port = msg_arg2
            udpSerSock.sendto(
                ("%d|%s|%s" % (9, "hello", " ")).encode(), (msg_arg1, int(msg_arg2))
            )

        elif msg_type == 5:
            print(f"{datetime.now()} - peer msg received: {msg_arg1}")
            udpSerSock.sendto(
                ("%d|%s|%s" % (8, msg_arg1, " ")).encode(), (peer_ip, int(peer_port))
            )

        elif msg_type == 6:
            print(f"{datetime.now()} - peer msg: ", msg_arg1, msg_arg2)
            udpSerSock.sendto(
                ("%d|%s|%s" % (7, msg_arg1, msg_arg2)).encode(),
                (peer_ip, int(peer_port)),
            )

        elif msg_type == 7:  # Single Ping response
            print(
                f"{datetime.now()} - ping received:  { (time.time() - tmpTime)}"
            )
            device.loop()
            if device.is_connected():
                device.send_state(
                    {
                        "epoch": time.time(),
                        "resp_time": (time.time() - tmpTime),
                        "cellband": sys.argv[1],
                    }
                )
                counter+=1
            else:
                print(f"{datetime.now()} - error Type!", str(data))
            if counter==10:
                endprogram=True
            cmd_state = 4  # Get User Input for next action

        elif msg_type == 8:
            if validation_msg == msg_arg1:
                print(f"{datetime.now()} - valid msg '{msg_arg1}' recevied")
            else:
                print(
                    f"{datetime.now()} - Invalid msg received '{msg_arg1}' should be {validation_msg} "
                )
            cmd_state = 4  # Get User Input for next action


def input_with_default(prompt, default):
    name = input(f"{prompt} [{default}]>>")
    if name != "":
        return name
    return default


try:

    heat_thread = threading.Thread(target=heartbeat)
    heat_thread.setDaemon(True)
    heat_thread.start()

    rev_thread = threading.Thread(target=revMsg)
    rev_thread.setDaemon(True)
    rev_thread.start()
    time.sleep(1)

except:
    print("Error: unable to start thread")

# ========================
host_name = "Noname"
# Execute the 0, 1, 2, 3 commands in turn to complete the p2p connection and chat directly
print(f"Press [Enter] to accept defaults.")
while True:
    if endprogram:
        print('done')
        break
    # comd = input("Commend[0,1,2,3,4]>>")
    # query online host
    strip_cmd = str(cmd_state)
    # strip_cmd = str(comd).strip()
    if strip_cmd == "0":
        # host name defaults to client1 unless input is given
        host_name = input_with_default("host name", "client1")
        validation_msg = f"host name is {host_name}"

        # peer name default to client2 unless input is given
        peer_name = input_with_default("peer name", "client2")

        udpSerSock.sendto((f"0|{str(host_name).strip()}| ").encode(), server_addr)
        cmd_state=2
    elif strip_cmd == "1":
        print("get online host...")
        udpSerSock.sendto(("%d|%s|%s" % (1, " ", " ")).encode(), server_addr)

    elif strip_cmd == "2":
        if get_peer_counter < peer_counter_limit:
            print(f"get peer ip for {peer_name}")
            udpSerSock.sendto(
                ("%d|%s|%s" % (2, str(peer_name).strip(), " ")).encode(), server_addr
            )
        else:
            print(f"peer check limit reached ({peer_counter_limit})")
            break
        time.sleep(3)
        cmd_state=3

    elif strip_cmd == "3":
        print(f"{datetime.now()} - sending validation message")
        udpSerSock.sendto(
            ("%d|%s|%s" % (5, str(validation_msg).strip(), " ")).encode(),
            (peer_ip, int(peer_port)),
        )

    elif strip_cmd == "4":
        next_cmd = str(input("5-Single Ping\n6-Cont Ping\n10-Exit App\n>>"))
        if (next_cmd == "5") | (next_cmd == "6") | (next_cmd == "10"):
            cmd_state = next_cmd
        elif next_cmd == "2":
            get_peer_counter = 0
            cmd_state = next_cmd

    elif strip_cmd == "5":
        print(f"{datetime.now()} - Sending Ping")
        udpSerSock.sendto(
            ("%d|%s|%s" % (6, f"{time.time()}", " ")).encode(),
            (peer_ip, int(peer_port)),
        )

    elif strip_cmd == "6":
        print(
            f"{datetime.now()} - Sending constant pings every 1 sec for 10 seconds.  Use CTRL-C to stop"
        )
        while True:
            tmpTime = time.time()
            udpSerSock.sendto(
                ("%d|%s|%s" % (6, f"{time.time()}", " ")).encode(),
                (peer_ip, int(peer_port)),
            )
            #time.sleep(1)

    elif strip_cmd == "10":
        print(f"{datetime.now()} - Exiting application")
        break

    time.sleep(sleep_time)
    # if str(comd).strip() == "exit":
    #     print("exit!")
    #     break
udpSerSock.close()
{"mode":"full","isActive":false}
