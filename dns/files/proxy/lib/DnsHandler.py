###########################################
# Author: Alexander Stock                 #
# ID: i532593                             #
# Mail: a.stock@sap.com                   #
###########################################

"""
Module for setting up a UDP server and catching notify messages
"""

import socketserver
import logging
from dnslib import DNSRecord, DNSError
from dnslib.dns import RR



class DNSHandler(socketserver.BaseRequestHandler):

    '''
    Class for intercepting DNS sync requests
    '''

    def send_data(self, data):
        """return answer to client"""
        return self.request[1].sendto(data, self.client_address)

    def handle(self):
        """handle incoming UDP DNS requests"""
        data = self.request[0].strip()
        try:
            myRequest = DNSRecord.parse(data)
        except DNSError as e:
            myRequest = None
            logging.critical("No valid DNS request.")
            logging.critical(e)
        if self.server.myDnsCMD:
        # Check if its a NOTIFY operation
            if myRequest is not None:
                if myRequest.header.get_opcode() == 4:
                    myQuery = myRequest.get_q()
                    myDomain = myQuery.get_qname()
                    targets = self.server.myDnsCMD.query_record(
                    f"tasks.{self.server.myDnsCMD.service}", 'A')
                    for target in targets:
                        checkResult = self.server.myDnsCMD.query_record(str(myDomain),
                        'SOA', str(target))
                        if checkResult is not None and len(checkResult) == 0:
                            self.server.myDnsCMD.push_zone(str(target), myDomain)
                        if checkResult is not None and len(checkResult) > 0:
                            self.server.myDnsCMD.update_zone(target, myDomain)
                # This part is for healthchecking of the master containers proxy process
                # On regular DNS requests we send back a dummy answer we can check on.
                elif myRequest.header.get_opcode() == 0:
                    logging.info("Retrieved regular DNS query, returning dummy result.")
                    reply = myRequest.reply()
                    reply.add_answer(*RR.fromZone("i.am.fine. 60 A 1.2.3.4"))
                    self.send_data(reply.pack())
                else:
                    logging.critical("No valid NOTIFY header found.")
        else:
            logging.critical("No DnsCMD object found for interacting with our slave instances.")


def get_server(ip, port, Handler):
    """return server object which then can be started"""
    return socketserver.UDPServer((ip, port), Handler)
