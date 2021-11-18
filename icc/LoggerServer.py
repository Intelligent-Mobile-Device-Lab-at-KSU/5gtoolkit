# LoggerServer.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app receives logging control messages from 5gtoolkit tests, and logs them to a .csv file.

# The intended use is to run this app on a server.

# 1. Log into your server.
# 2. Download the 5gtoolkit git repo.
# 3. Edit the config.json file so that logger server ip and port are what you desire.
# 4. python3 LoggerServer.py

import socket
import sys
import json

f = open('config.json',)
conf = json.load(f)
f.close()

server_addr = (conf["logger_server"]["ip"], conf["logger_server"]["port"])

# Create a TCP/IP socket
tcpServerSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Bind the socket to the port
tcpServerSock.bind(server_addr)
print("LoggerServer listening on " + server_addr[0] + ":" + str(server_addr[1]))

# Listen for incoming connections
tcpServerSock.listen(1)
runAll = False
while True:
    # Wait for a connection
    print("Waiting for a connection...")
    connection, client_address = tcpServerSock.accept()
    try:
        print("connection from " + client_address[0])
        # Receive the data in small chunks and retransmit it
        while True:
            data = connection.recv(65000)
            data = data.decode().split(":")
            #print("received %s" % (data))

            if ("NEW_LOG" in data[0]):
                print("NEW_SCRIPT_LOG")
                running_fname = data[1]
                print("fopen with append filename.csv")
                print(running_fname+"\n")
                connection.sendall(str("BEGIN").encode())
            else:
                # log data
                print(data[0])
                connection.sendall(str("DONE").encode())
                print("closing connection")
                connection.close()
                print("saving file")
                break

            if data == "RUNALL":
                runAll = True

    finally:
        # Clean up the connection
        connection.close()
