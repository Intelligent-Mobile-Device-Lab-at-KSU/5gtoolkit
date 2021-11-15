# fivegtoolkit.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.
#
# This is intended for use in Termux.
# Not that the python command for Termux is by default python3
# You can add an argument: 3 to call: python3
# Otherwise the default is: python (because this app assumes Termux)
#
# Example (not on Termux): python3 fivegtoolkit.py 3, will run all scripts with a subprocess call: python3 NetworkSounder.py
# Example (on Termux): python fivegtoolkit.py, will run all scripts with a subprocess call: python NetworkSounder.py
#
# Choose an option:
# A - Find 5G Towers
# 	1. NetworkSounder.py
#
# B - Device to EndPointServer test
# 	2. Echo_RTT_Client.py <pktsize> <#pkts>
# 	3. EndPoint_DL_Goodput.py <pktsize> <duration>
# 	4. EndPoint_UL_Goodput.py <pktsize> <duration>
# 	5. EndPoint_DL_Jitter.py <pktsize> <duration>
# 	6. EndPoint_UL_Jitter.py <pktsize> <duration>
#
# C - Peer Relay test
# 	7. RelayToPeerRTT.py a|b <pktsize> <#pkts>
# 	8. RelayToPeerJitter.py a|b <pktsize> <duration>
# 	9. RelayToPeerGoodput.py a|b <pktsize> <duration>
#
# D - Hole-Punch Peer test
# 	a. HolePunchPeerRTT.py a|b <pktsize> <#pkts>
# 	b. HolePunchPeerJitter.py a|b <pktsize> <duration>
# 	c. HolePunchPeerGoodput.py a|b <pktsize> <duration>
#
# E - Measurement Suite (saves to CSV on each device/server)
# 	w. RunEveryThing.py (must have ALL servers running)
# 	x. AllDevice2EndPointTests.py (must have EndPointServer running)
# 	y. AllPeerRelayTests.py (must have RendezvousRelayServer running)
# 	z. AllHolePunchPeerTest.py (must have HolePunchServer running)
#
# 	For Echo:
# 	Varies packet size from 1 10 100 1000 10000 30000 65000
# 	Varies #pkts from 1 10 100 1000
# 	Client A: Total 28 results (mean, std.dev, min, max)
# 	Client B: Total 28 results (logs all data [currenttimestamp vs elapsed])
#
# 	For Jitter:
# 	Varies packet size from 1 10 100 1000 10000 30000 65000
# 	Varies duration from 1 10 20 30
# 	Client A: Total 28 results (mean, std.dev, min, max)
# 	Client B: Total 28 results (logs all data [currenttimestamp and epochs] [currenttimestamp and delays])
#
# 	For Goodput:
# 	Varies packet size from 1 10 100 1000 10000 30000 65000
# 	Varies duration from 1 10 20 30
# 	Client A: Total 28 results (mean, std.dev, min, max)
# 	Client B: Total 28 results (logs all data [currenttimestamp and totalBytesRecvd])

import os
import sys
import subprocess

menu = {}
menu['m1']="A - Find 5G Towers"
menu['1']="NetworkSounder.py"
menu['m2']="B - Device to Relay tests"
menu['2']="Echo_RTT_Client.py"
menu['3']="EndPoint_DL_Goodput.py"
menu['4']="EndPoint_UL_Goodput.py"
menu['5']="EndPoint_DL_Jitter.py"
menu['6']="EndPoint_UL_Jitter.py"
menu['m3']="C - Peer Relay tests"
menu['7']="RelayToPeerRTT.py"
menu['8']="RelayToPeerJitter.py"
menu['9']="RelayToPeerGoodput.py"
menu['m4']="D - Hole-Punch Peer tests"
menu['a']="HolePunchPeerRTT.py"
menu['b']="HolePunchPeerJitter.py"
menu['c']="HolePunchPeerGoodput.py"
menu['m5']="E - Measurement Suite (saves to CSV on each device/server)"
menu['w']="RunEveryThing.py"
menu['x']="AllDevice2EndPointTests.py"
menu['y']="AllPeerRelayTests.py"
menu['z']="AllHolePunchPeerTest.py"

argumentType1_echo_endpointtest = ["2"]
argumentType2_echo_relayorholepunch = ["7", "a"]
argumentType3_duration_endpointtest = ["3","4","5", "6"]
argumentType4_duration_peer = ["8","9","b","c"]

pthonver = 'python'
if len(sys.argv) == 2:
    pthonver = 'python3'

windowsPythonPath = "C:\\Users\\bkihei\\PycharmProjects\\5gtoolkit\\venv\\Scripts\\python.exe"
pthonver=windowsPythonPath
print(pthonver)

command = ''
while True:
    params = {
        "pktsize": 0,
        "numpkts": 0,
        "username": '',
        "duration": 0
    }
    options = menu.keys()
    print(options)
    availOptions = []
    for entry in options:
        availOptions.append(entry)
        if "m" not in entry:
            print("\t" + entry + " - " + menu[entry])
        else:
            print(menu[entry])

    selection = input("Please make a selection (q to exit): ")
    if selection in availOptions:
        command = '{} {}'.format(pthonver, menu[selection])
        if selection in argumentType1_echo_endpointtest:
            y=input("Please input: <pktsize> <#ofpkts>: ")
            y=y.split(" ")
            params["pktsize"] = y[0]
            params["numpkts"] = y[1]
            command = "{} {} {}".format(command, params["pktsize"], params["numpkts"])
        elif selection in argumentType2_echo_relayorholepunch:
            y = input("Please input: a|b <pktsize> <duration>: ")
            y = y.split(" ")
            if y[0] == 'a':
                params["username"] = 'a'
                params["pktsize"] = y[1]
                params["duration"] = y[2]
                command = "{} {} {} {}".format(command, params["username"], params["pktsize"], params["numpkts"])
            else:
                params["username"] = 'b'
                command = "{} {}".format(command, params["username"])
        elif selection in argumentType3_duration_endpointtest:
            y = input("Please input: <pktsize> <duration>: ")
            y = y.split(" ")
            params["pktsize"] = y[0]
            params["duration"] = y[1]
            command = "{} {} {}".format(command, params["pktsize"], params["duration"])
        elif selection in argumentType4_duration_peer:
            y = input("Please input: a <pktsize> <duration> or just b: ")
            y = y.split(" ")
            if y[0] == 'a':
                params["username"] = 'a'
                params["pktsize"] = y[1]
                params["duration"] = y[2]
                command = "{} {} {} {}".format(command, params["username"], params["pktsize"], params["duration"])
            else:
                params["username"] = 'b'
                command = "{} {}".format(command, params["username"])
    elif selection == "q":
        break
    else:
        print("Selection Invalid.")
        selection = input("Press any key to make another selection...")
        continue

    exitToolkit = False
    while True:
        p = subprocess.call(command, shell=True)
        x=input("Run again (y/n/c/q)?")
        if x=='q':
            exitToolkit = True
            break
        elif x=='y':
            continue
        elif x=='n':
            break
        elif x=='c':
            command = '{} {}'.format(pthonver, menu[selection])
            if selection in argumentType1_echo_endpointtest:
                y = input("Please input: <pktsize> <#ofpkts>: ")
                y = y.split(" ")
                params["pktsize"] = y[0]
                params["numpkts"] = y[1]
                command = "{} {} {}".format(command, params["pktsize"], params["numpkts"])
            elif selection in argumentType2_echo_relayorholepunch:
                y = input("Please input: a|b <pktsize> <duration>: ")
                y = y.split(" ")
                if y[0] == 'a':
                    params["username"] = 'a'
                    params["pktsize"] = y[1]
                    params["duration"] = y[2]
                    command = "{} {} {} {}".format(command, params["username"], params["pktsize"], params["numpkts"])
                else:
                    params["username"] = 'b'
                    command = "{} {}".format(command, params["username"])
            elif selection in argumentType3_duration_endpointtest:
                y = input("Please input: <pktsize> <duration>: ")
                y = y.split(" ")
                params["pktsize"] = y[0]
                params["duration"] = y[1]
                command = "{} {} {}".format(command, params["pktsize"], params["duration"])
            elif selection in argumentType4_duration_peer:
                y = input("Please input: a <pktsize> <duration> or just b: ")
                y = y.split(" ")
                if y[0] == 'a':
                    params["username"] = 'a'
                    params["pktsize"] = y[1]
                    params["duration"] = y[2]
                    command = "{} {} {} {}".format(command, params["username"], params["pktsize"], params["duration"])
                else:
                    params["username"] = 'b'
                    command = "{} {}".format(command, params["username"])
    if exitToolkit:
        break

