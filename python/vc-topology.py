#!/usr/bin/python

# Author: Ryan Barnes [barnesry@juniper.net]
# Date  :    Nov 29, 2016
# 
# Description: 
#   Pulls virtual-chassis information via XML-RPC and parses into Python objects for
#   topology parsing
#
# Version History
#   0.1     Nov 29, 2016

from jnpr.junos import Device
from lxml import etree as etree
from collections import defaultdict

class VCMemberSwitch(object):
    """ Describes a VC Member Switch in a stack """
    id_index = defaultdict(list)

    def __init__(self, id, serial_number=None, model=None, role=None, neighbor_list=None):
        self.id = id
        VCMemberSwitch.id_index[id].append(self)    # builds an indexed list of objects by ID
        self.serial_number = serial_number
        self.model = model
        self.role = role
        if neighbor_list:
            self.neighbor_list = neighbor_list
        else:
            self.neighbor_list = []

    @classmethod
    def find_by_id(cls, id):
        return VCMemberSwitch.id_index[id]

    def add_neighbor(self, VCInterface):
        self.neighbor_list.append(VCInterface)

    def describe_neighbors(self):
        for neighbor in self.neighbor_list:
            remote_switch = VCMemberSwitch.id_index[neighbor.remote_switch_id][0]
            print remote_switch.serial_number + ":" + neighbor.local_vc_port_name

class VCInterface(object):
    """ Describes a VC interface on a VC member """
    def __init__(self):
        self.local_switch_id = None
        self.local_vc_port_name = None
        self.remote_switch_id = None
        self.remote_vc_port_name = None

    def describe_parent(self):
        """ Returns the VCMemberSwitch attached to this interface """
        for switch in VCMemberSwitch.find_by_id(self.local_switch_id):
            print "Parent Serial : {}".format(switch.serial_number)



def print_summary(member_list):
    """ Expect an array of objects containing VC member info """
    print "SUMMARY"
    print "{:5} {:15} {:20} {:15}".format("id", "serial_num", "model", "role")
    print "-" * 40
    for member in member_list:
        print "{:5} {:15} {:20} {:15}".format(member.id,
                                              member.serial_number,
                                              member.model,
                                              member.role)
        #print "Neighbors (id:remote_port_name)"
        #print member.describe_neighbors()

def main():

    with Device(host='192.168.57.100', user='root', passwd='junos123') as dev:
        print "Connecting to...{}".format(dev.hostname)
        dev.open()
        print "Success!"

        vci = dev.rpc.get_virtual_chassis_information(detail=True)
        # vci_stats = dev.rpc.get_virtual_chassis_port_statistics()
        # vc = dev.rpc.get_virtual_chassis_device_topology()

        vc_member_list = []

        # parse get_virtual_chassis_information_detail
        for member in vci.xpath('//virtual-chassis-information/member-list/member'):
            id = member.find('member-id').text
            serial_number = member.find('member-serial-number').text
            model = member.find('member-model').text
            role = member.find('member-role').text

            vc_member = VCMemberSwitch(id=id,
                                       serial_number=serial_number,
                                       model=model,
                                       role=role)

            # enumerate connected neighbors
            for neighbor in member.xpath('./neighbor-list/neighbor'):
                interface = VCInterface()
                interface.local_vc_port_name = neighbor.find('neighbor-interface').text
                interface.remote_switch_id = neighbor.find('neighbor-id').text

                vc_member.add_neighbor(interface)

            vc_member_list.append(vc_member)

        print "Members : {}".format(len(vc_member_list))
        print_summary(vc_member_list)

        # for switch in VCMemberSwitch.find_by_id('1'):
        #     print "Parent Serial : {}".format(switch.serial_number)
        #     print "Neighbor List : "
        #     switch.describe_neighbors()

# executes only if not called as a module
if __name__ == "__main__":
   main()