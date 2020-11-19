#!/usr/bin/python3

###########################################
# Author: Alexander Stock                 #
# ID: i532593                             #
# Mail: a.stock@sap.com                   #
###########################################
"""
This script will be started inside the bind slave container after bind service is started.
It periodically checks if the local configured zones are still available
on the master with a SOA query.
If a zone is missing on the master it also gets deleted on the slave.
"""

import logging
import sys
import os
# Our Stuff
from lib.DnsCMD import DnsCMD


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

# Build our RNDC/CMD object
myDnsCMD = DnsCMD(
                service=os.environ["mySlaveService"],
                slaveKey=os.environ["mySlaveKey"],
                nzfFile=os.environ["nzfFile"],
                anycastIPs=os.environ["anycastIPs"]
                )

# Start our loop
myDnsCMD.slave_cleanup()
