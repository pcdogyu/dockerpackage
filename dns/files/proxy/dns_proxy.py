#!/usr/bin/python3

###########################################
# Author: Alexander Stock                 #
# ID: i532593                             #
# Mail: a.stock@sap.com                   #
###########################################

"""
This script will be started inside the bind master container after bind service is started.
This script does two things:

1. Start UDP server thread for handling connections on port 1053
2. Start loop thread which periodically checks all slave containers
for the correct zone configuration.
This is helpful when the slave docker service gets scaled up
and new blank slave nodes gets deployed.
"""

import logging
import sys
import time
import os
import threading
# Our Stuff
from lib.DnsCMD import DnsCMD
from lib.DnsHandler import DNSHandler, get_server


# Get my logging object
logging.basicConfig(stream=sys.stdout,
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Checking Environment variables
neededParameters = ["mySlaveService",
                    "mySlaveKey",
                    "nzfFile",
                    "anycastIPs"]
for myParameter in neededParameters:
    if not os.environ[myParameter]:
        logging.critical(f"Parameter {myParameter} is not set. Aborting.")
        sys.exit(1)



# Build our RNDC/CMD object for the sync loop
myDnsCMD = DnsCMD(
    service=os.environ["mySlaveService"],
    slaveKey=os.environ["mySlaveKey"],
    nzfFile=os.environ["nzfFile"],
    anycastIPs=os.environ["anycastIPs"]
)
# Build a second RNDC/CMD object for the server loop
# to avoid future collisions with concurrent threads
myDnsCMDServer = DnsCMD(
    service=os.environ["mySlaveService"],
    slaveKey=os.environ["mySlaveKey"],
    nzfFile=os.environ["nzfFile"],
    anycastIPs=os.environ["anycastIPs"]
)
# Create the thread for our sync loop. Target is sync method of RNDC object
loopThread = threading.Thread(target=myDnsCMD.sync_master_slave)
# Build our UDP server which speaks DNS with injecting our UDP handler
server = get_server('127.0.0.1', 1053, DNSHandler)
# Set our RNDC/CMD object
server.myDnsCMD = myDnsCMDServer
# Create thread for our server
serverThread = threading.Thread(target=server.serve_forever)
# Let it run in daemon mode
serverThread.daemon = True

# Start threads
try:
    logging.info("Sync loop started")
    loopThread.start()
    logging.info("UDP server started")
    serverThread.start()
    while True:
        time.sleep(5000)
except (KeyboardInterrupt, SystemExit):
    server.shutdown()
    server.server_close()
    sys.exit()
