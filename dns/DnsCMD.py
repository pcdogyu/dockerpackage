###########################################
# Author: Alexander Stock                 #
# ID: i532593                             #
# Mail: a.stock@sap.com                   #
###########################################

"""
Module for managing DNS zones
"""

import subprocess
import logging
import time
import re
import dns.message
import dns.query


class DnsCMD:

    '''
    Class for managing DNS Zones on Bind servers

    Parameters
    ----------
    service : str
        Name of the Swarm DNS Slave Service
    SlaveKey : str
        Path to our slave key
    nzfFile : str
        Path to nzfFile which includes all configured zones
    anycastIP : str
        IP which will be utilized for sync requests from slave to master
    '''

    def __init__(self,
                 service=None,
                 slaveKey=None,
                 nzfFile=None,
                 anycastIPs=None):
        self.service = service
        self.SlaveKey = slaveKey
        self.nzfFile = nzfFile
        self.masterPort = 1153
        self.nameservers = self.get_local_nameservers()
        self.anycastIPArray = anycastIPs.replace(" ", "").split(",")
        self.anycastIPString = "; ".join([f"{ip} port {self.masterPort}"
                                        for ip in self.anycastIPArray])

    def get_local_nameservers(self, file="/etc/resolv.conf"):
        """Get all nameservers from containers resolv.conf"""
        myNameservers = []
        myFile = open(file)
        myLines = myFile.readlines()
        myFile.close()
        for line in myLines:
            tempArray = line.split()
            if len(tempArray) > 1:
                if tempArray[0] == "nameserver":
                    myNameservers.append(tempArray[1])
        return myNameservers

    def query_record(self, searchTerm, recordType, dnsServer=None, port=53 ):
        """Query DNS records with recordType"""
        ipList = None
        if dnsServer is None:
            if  len(self.nameservers) > 0:
                dnsServer = self.nameservers[0]
            else:
                logging.error("No nameservers available for the query.")
        if dnsServer is not None:
            myQuery = dns.message.make_query(searchTerm, recordType)
            try:
                result = dns.query.udp(
                                myQuery,
                                dnsServer,
                                timeout=3,
                                port=port,
                                one_rr_per_rrset=True)
                ipList = [ ip[0] for ip in result.answer]
            except dns.exception.Timeout as e:
                logging.error(e)
            except dns.exception.DNSException as e:
                ipList = []
                logging.error(e)
        return ipList

    def get_local_zones(self):
        """read local zones configured on the instance"""
        # We use python internals here to avoid missing error handling in a pipe with AWK and sed
        returnArray = []
        try:
            f = open(self.nzfFile, "r")
            text = f.readlines()
            f.close()
        except OSError:
            logging.info(f"Could not find: {self.nzfFile}")
            text = None

        # This is a workaround because rndc sometimes forgets
        # to add a newline to the entries in the nzf file
        if text is not None:
            for line in text:
                # Do we have a line with zone entries
                if re.match("^zone", line):
                    # We split on each zone
                    tempLines = line.split("zone \"")
                    # We loop through all entries except the first (empty string)
                    for tempLine in tempLines[1:]:
                        # We split on whitespace
                        temparray = tempLine.split(" ")
                        # We take the first element and remove all " chars
                        zone = temparray[0].replace("\"", "")
                        # We add the zone to our array
                        returnArray.append(zone)

        return returnArray


    def push_zone(self, target, zone):
        """push new zone via rndc"""
        cmd = f"rndc -s {target} -k {self.SlaveKey} -p 953 addzone {zone} '{{ type slave; " \
        + f"file \"dyn/{zone}\"; masters {{ { self.anycastIPString };  }};}};'"

        result, returncode = self.rndc_cmd(cmd)
        if returncode == 0:
            logging.info(f"Zone {zone} created on {target}.")
            cmd = f"rndc -s {target} -k {self.SlaveKey} -p 953 reconfig"
            result, returncode = self.rndc_cmd(cmd)
            if returncode == 0:
                logging.info(f"Zone {zone} reconfigured on {target}.")
                cmd = f"rndc -s {target} -k {self.SlaveKey} -p 953 reload {zone}"
                result, returncode = self.rndc_cmd(cmd)
                if returncode == 0:
                    logging.info(f"Zone {zone} reloaded on {target}.")
        else:
            logging.error(f"Failed to push zone {zone} to {target}: {result}")


    def delete_zone(self, target, zone):
        """delete zone via rndc"""
        cmd = f"rndc -s {target} -k {self.SlaveKey} -p 953 delzone {zone}"
        result, returncode = self.rndc_cmd(cmd)
        if returncode == 0:
            logging.info(f"Zone {zone} deleted.")
        else:
            logging.error(f"Failed to delete zone {zone} from {target}: {result}")

    def update_zone(self, target, zone):
        """update zone via rndc"""
        cmd = f"rndc -s {target} -k {self.SlaveKey} -p 953 reload {zone}"
        result, returncode = self.rndc_cmd(cmd)
        if returncode == 0:
            logging.info(f"Zone {zone} reloaded on {target}.")
        else:
            logging.error(f"Failed to update zone {zone} on {target}: {result}")

    def rndc_cmd(self, cmd):
        """encapsulated rndc function"""
        returncode = 0
        result = None
        try:
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT,
            encoding='ascii')
        except subprocess.CalledProcessError as e:
            # Check for connection
            logging.critical(f"RNDC error: {str(e.output)}")
            returncode = 1
        return result, returncode

    def sync_master_slave(self):
        """loop function for periodically configuring zones on all slaves
        (runs on master with dns-proxy)"""
        while True:
            masterZones = self.get_local_zones()
            targets = self.query_record(f"tasks.{self.service}", 'A')
            for target in targets:
                # Check if all master zones are configured on the slaves
                for mZone in masterZones:
                    checkResult = self.query_record(mZone, 'SOA', str(target))
                    if checkResult is not None:
                        if len(checkResult) == 0:
                            self.push_zone(str(target), mZone)
            time.sleep(30)

    def slave_cleanup(self):
        """loop function for cleaning up old zones on slaves
        (runs on each slave with dns-cleanup.py)"""
        while True:
            masterFound = False
            for anycastIP in self.anycastIPArray:
                if masterFound is True:
                    break
                slaveZones = self.get_local_zones()
                # Check for current master
                masterTest = self.query_record(
                                    'localhost',
                                    'SOA',
                                    str(anycastIP),
                                    self.masterPort)
                if masterTest is not None:
                    masterFound = True
                    for myZone in slaveZones:
                        checkResult = self.query_record(
                                            myZone,
                                            'SOA',
                                            str(anycastIP),
                                            self.masterPort)
                        if checkResult is not None and len(checkResult) == 0:
                            self.delete_zone('127.0.0.1', myZone)
                else:
                    logging.critical(
                    f"Master IP address { anycastIP } seems to be down. "\
                    "Trying next one.")
            if masterFound is False:
                logging.critical("No master ip from our list could be contacted!")
            time.sleep(30)
