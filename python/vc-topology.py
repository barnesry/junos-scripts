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

# barnesry-mbp:python barnesry$ ./vc-topology.py
# Connecting to...192.168.57.100
# Success!
# Members : 2
# SUMMARY
# id    serial_num      model                role
# ----------------------------------------
# 0     CT0213051609    ex2200-48p-4g        Master*
# 1     GP0214373311    ex2200-c-12t-2g      Linecard

# Back Plane Utilization Statistics
# ---------------------------------------------

# Member0 of type ex2200-48p-4g connected to:
# Member1 via vcp-255/0/46   	 UtilIn:0% UtilOut:0%
# Member1 via vcp-255/0/47   	 UtilIn:0% UtilOut:0%

# Member1 of type ex2200-c-12t-2g connected to:
# Member0 via vcp-255/1/0    	 UtilIn:0% UtilOut:0%
# Member0 via vcp-255/1/1    	 UtilIn:0% UtilOut:0%


from jnpr.junos import Device
from lxml import etree as etree
from collections import defaultdict, OrderedDict

HOST = '192.168.57.100'
USER = 'root'
PASS = 'junos123'


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
        """ Returns a list containing switch object by ID """
        return VCMemberSwitch.id_index[id]

    def add_neighbor(self, VCInterface):
        self.neighbor_list.append(VCInterface)

    def describe_neighbors(self):
        neighbors = {}
        for neighbor in self.neighbor_list:
            remote_switch = VCMemberSwitch.id_index[neighbor.remote_switch_id][0]
            neighbors[remote_switch.id]
            remote_sw
            print remote_switch.id + " via " + neighbor.local_vc_port_name

    def describe_vcp_ports(self):
        """ Returns list of local vcp ports and associated neighbors """
        ports = {}
        for neighbor in self.neighbor_list:
            ports[neighbor.local_vc_port_name] = {
                'remote_switch_id' : neighbor.remote_switch_id
            }
        return ports

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

    def get_stats(self, interface_name):
        """ Returns stats for a given vc_port

            Input : VCInterface object
            Output : VCInterface object
        """
        pass    # not sure how to pass connection object in yet





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

    with Device(host=HOST, user=USER, passwd=PASS) as dev:
        print "Connecting to...{}".format(dev.hostname)
        dev.open()
        print "Success!"

        vci = dev.rpc.get_virtual_chassis_information(detail=True)
        # vc = dev.rpc.get_virtual_chassis_device_topology()
        vci_stats = dev.rpc.get_virtual_chassis_port_statistics()

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

        # Report VC Port Utilization for each VC port attached to each VC Member
        print "\nBack Plane Utilization Statistics"
        print "-"* 45

        keys = sorted(VCMemberSwitch.id_index.keys())
        for key in keys:
            switch = VCMemberSwitch.find_by_id(key)[0]
        # for index, switch_list in VCMemberSwitch.id_index.iteritems():
            # switch = switch_list[0]
            # print "Parent Serial : {}".format(switch.serial_number)

            ports = switch.describe_vcp_ports()
            print "\nMember{} of type {} connected to:".format(switch.id, switch.model)

            for remote_vc_port_name, v in ports.iteritems():
                xpath_string = '//statistics-port-list/statistics[port-name[text() = "' + \
                    remote_vc_port_name + '"]]'
                result = vci_stats.xpath(xpath_string)
                util_in = result[0].find('input-utilization').text
                util_out = result[0].find('output-utilization').text
                # print etree.tostring(result[0])
                print "Member{} via {:15}\t UtilIn:{}% UtilOut:{}%".format(v['remote_switch_id'],
                                                                           remote_vc_port_name,
                                                                           util_in,
                                                                           util_out)


# executes only if not called as a module
if __name__ == "__main__":
   main()