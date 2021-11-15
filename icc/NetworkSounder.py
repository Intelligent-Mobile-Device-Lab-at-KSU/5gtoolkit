# NetworkSounder.py
# Billy Kihei (c) 2021
# Intelligent Mobile Device Lab @ Kennesaw State University
# Part of the 5Gtoolkit for testing commercial 5G networks.

# This app simply sends the character '0' to a non-existent UDP server.
# The purpose of this app is to activate the cellular modem such that
# the modem will attach to a 5G mmWave site.

# The intended use is to run this app in Termux, then put the phone in service mode
# to see what 5G bands the phone is attaching to.

# 1. Open Termux.
# 2. Download the 5gtoolkit git repo.
# 3. python NetworkSounder.py
# 4. On Samsung Android phone (T-Mobile) type on phone keypad: *#0011#
# 5. Look at the NR band the modem attaches to.

import socket
import sys
import signal
import time

tx=0
server_addr = ("8.8.8.8", 53)
udpSerSock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def signal_handler(sig, frame):
    udpSerSock.close()
    print('\n')
    print("%d bytes sent!\n" % (tx))
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print('Sounding continuously...'
      '\nOpen Service Mode: '
      '\n\tSamsung with 5G dial: *#0011#'
      '\n\t\tObserve the NR_BAND field '
      '\n\tiPhone with 5G dial: *3001#12345#*'
      '\nCtrl+C to stop.')
while True:
    udpSerSock.sendto(str.encode("0"), server_addr)
    tx+=len(str.encode("0"))
    time.sleep(.1)