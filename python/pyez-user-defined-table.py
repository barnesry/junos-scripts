#! /usr/bin/python

# L2NG EthernetTable test

from jnpr.junos import Device
from jnpr.junos.factory.factory_loader import FactoryLoader
import yaml
import argparse, logging, getpass, sys

yaml_data="""
---
L2ngEthernetSwitchingTable:
  rpc: get-ethernet-switching-table-information
  item: l2ng-mac-entry
  key: l2ng-l2-mac-address
  view: L2ngEthernetSwitchingTableView
L2ngEthernetSwitchingTableView:
  fields:
    vlan: l2ng-l2-mac-vlan-name
    mac_address: l2ng-l2-mac-address
    flags: l2ng-l2-mac-flags
    age: l2ng-l2-mac-age
    logical_interface: l2ng-l2-mac-logical-interface
"""

def main(args):

    host = args.host
    user = args.user
    password = args.password
        
    dev = Device(host=args.host, user=args.user, password=args.password, gather_facts=True)
    dev.open()

    print dev.facts

    globals().update(FactoryLoader().load(yaml.load(yaml_data)))

    ethernet_table = L2ngEthernetSwitchingTable(dev)
    print "Retriving ethernet table..."
    ethernet_table.get()

    # debug
    print ethernet_table
        
    for mac in ethernet_table:
            print 'vlan: ', mac.vlan
            print 'mac_address: ', mac.mac_address
            print 'flags: ', mac.flags
            print 'age: ', mac.age
            print 'logical_interface: ', mac.logical_interface

    dev.close()


# executes only if not called as a module
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", dest="host", help="target for connection", required=True)
    parser.add_argument("--user", dest="user", help="username to connect with", required=False)
    args = parser.parse_args()

    password = getpass.getpass()
    args.password = password

    # Change ERROR to INFO or DEBUG for more verbosity
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

    # run our main program
    main(args)