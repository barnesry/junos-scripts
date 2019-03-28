from jnpr.junos.device import Device
from jnpr.junos.factory.factory_loader import FactoryLoader
import yaml
import jxmlease
import argparse
from jnpr.junos.exception import *
from pprint import pprint


# This on-box op script returns concatenated info on BGP peer state for multiple VRFs
# minimum supported JunOS version is 16.1 but tested on 17.4R1

# Required configuration to execute this
# op {
#     file bgpneighbors.py;
# }
# language python;

# op bgpneighbors.py format txt
# ROUTING-INSTANCE                   PEER-IP           PEER-STATE
# ---------------------------------------------------------------------------
# VRF1.inet.0                        179.254.1.254     Established


# op bgpneighbors.py format xml
# <bgp-information>
#   <bgp-rib>
#     <name>VRF1.inet.0</name>
#     <peerip>179.254.1.254</peerip>
#     <peerstate>Established</peerstate>
#   </bgp-rib>


tableView = """
---
BgpNeighborTable:
    rpc: get-bgp-summary-information
    item: bgp-peer/bgp-rib
    key: name
    view: _neighbor_tbl_view

_neighbor_tbl_view:
    fields:
        peerip: ../peer-address
        rib: name
        peerstate: ../peer-state
"""

globals().update(FactoryLoader().load(yaml.load(tableView)))

# Define arguments dictionary
arguments = {'format': 'Output format desired (xml|txt)'}


def print_txt(peers):
    ''' prints out the BGP neighbor structure to screen for user consumption'''
    print("{:35s}{:18s}{:20s}".format("ROUTING-INSTANCE", "PEER-IP", "PEER-STATE"))
    print("-"*75)

    for peer in peers:
        print("{:35s}{:18s}{:20s}".format(peer.rib,
                                        peer.peerip,
                                        peer.peerstate)) 

def print_xml(peers):
    ''' displays to screen in XML '''
    print("<bgp-information>")
    for peer in peers:
        print("  <bgp-rib>")
        print("    <name>{rib}</name>".format(rib=peer.rib))
        print("    <peerip>{peerip}</peerip>".format(peerip=peer.peerip))
        print("    <peerstate>{peerstate}</peerstate>".format(peerstate=peer.peerstate))
        print("  </bgp-rib>")
        print("</bgp-information>")         

def main():

    parser = argparse.ArgumentParser(description='This script scrapes "show bgp summary" and returns summarized results in a user specified format')

    for key in arguments:
        parser.add_argument(('-' + key), required=True, help=arguments[key])
    args = parser.parse_args()
    
    format = args.format

    dev = Device()
    try:
        dev.open()
        bgpSummary = BgpNeighborTable(dev)  # attach table to device
        peers = bgpSummary.get()

        if format == 'xml':
            print_xml(peers)
        elif format == 'txt':
            print_txt(peers)

        dev.close()
    except ConnectTimeoutError as e:
        print("The connection timed out.")

if __name__ == "__main__":
    main()        