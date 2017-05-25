#!/usr/bin/python

# Author: Ryan Barnes [barnesry@juniper.net]
# Date  :    May 25, 2017
#
# Description:
#   Retrieves dynamic MAC addresses from all switchports on an EX switch
#
# Version History
#   0.1     May 25, 2017
#
# Usage:
#
# barnesry-mbp:python barnesry$ ./mac-collection.py
# Connecting to...192.168.57.10
# Success!
# Collecting ethernet-switching table...
# ge-0/0/7.0      54:e0:32:90:c1:7f
# ge-0/0/8.0      00:26:08:07:e4:a2
# ge-0/0/10.0     38:c9:86:f0:cf:70
# ge-0/0/11.0     cc:e1:7f:8f:66:bf
# ge-0/0/9.0      54:e0:32:90:c1:41
#                 54:e0:32:90:c1:72
# -----------------------------
# INTERFACES WITH MULTIPLE MACS
# -----------------------------
# ge-0/0/9.0



from jnpr.junos import Device
from lxml import etree as etree
from collections import defaultdict

HOST = '192.168.57.10'
USER = 'root'
PASS = 'junos123'

def get_mac_table_by_interface(device):
    ''' Retrieves a list of MAC addresses of type LEARN from switch '''

    print "Collecting ethernet-switching table..."
    mac_table = device.rpc.get_ethernet_switching_table_information()

    # create a dict with interfaces as keys with macs listed by interface
    interface_list = defaultdict(list)

    # filter for mac-type "Learn" only
    for mac_address in mac_table.xpath('//mac-table-entry[mac-type[text() = "Learn"]]'):
        mac = mac_address.find('mac-address').text
        #mac_type = mac_address.find('mac-type').text
        #mac_vlan = mac_address.find('mac-vlan').text
        mac_interface = mac_address.find('mac-interfaces-list/mac-interfaces').text

        interface_list[mac_interface].append(mac)

    return interface_list



def print_mac_table(interface_list):
    ''' Prints MAC output to screen '''
    for interface, macs in interface_list.items():
        print("{:15}").format(interface),

        # if more than one on an interface
        if len(macs) > 1:
            for index, mac in enumerate(macs, start=1):
                if index == 1:
                    print mac
                else:
                    print("{:15} {}").format("", mac)
        else:
            # print the first one in the list
            print macs[0]


def ints_with_multiple_macs(interface_list):
    ''' returns a list of interfaces with multiple dynamic mac addresses learned'''
    print "-----------------------------"
    print "INTERFACES WITH MULTIPLE MACS"
    print "-----------------------------"
    for interface, macs in interface_list.items():
        if len(macs) > 1:
            print interface

def main():

    with Device(host=HOST, user=USER, passwd=PASS) as dev:
        print "Connecting to...{}".format(dev.hostname)
        dev.open()
        print "Success!"

        # retrieve list of mac addresses listed by interface
        interface_list = get_mac_table_by_interface(dev)

        #print interface_list
        print_mac_table(interface_list)

        # list of interfaces with more than one mac
        ints_with_multiple_macs(interface_list)


# executes only if not called as a module
if __name__ == "__main__":
    main()
