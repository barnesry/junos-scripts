#!/usr/bin/python

# # MIT License

# Copyright (c) 2017 Ryan Barnes

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#


import sys
import time
import datetime
import getpass
import argparse
import logging
from jnpr.junos.utils.start_shell import StartShell
from jnpr.junos.device import Device
from jnpr.junos.exception import ConnectError
from jnpr.junos.factory import loadyaml
from pprint import pprint
import re
import collections
from lxml import etree
import os
import subprocess
import time
import getpass      # used to retrieve userID
from pprint import pprint as pp

starttime=time.time()
user = getpass.getuser()

# host = '10.85.87.221'
# username = 'labroot'
# password = 'lab123'

#############
## CLASSES ##
#############
class Port(object):
    def __init__(self, logical_name, physical_name = '', brcm_pipe = '', brcm_drop_counter = ''):
        self.logical_name = logical_name
        self.physical_name = physical_name
        self.brcm_pipe = brcm_pipe
        self.brcm_drop_counter = brcm_drop_counter

    def __str__(self):
        return "OBJECT DUMP : log:{} phy:{} pipe:{} drop:{}".format(self.logical_name,
                                                                    self.physical_name,
                                                                    self.brcm_pipe,
                                                                    self.brcm_drop_counter)
        
class Switch(object):
    def __init__(self):
        self.ports = []

    def __str__(self):
            pp(vars(self))

    def add(self, port):
        logging.info("adding %s to switch...", port.logical_name)
        self.ports.append(port)
    
    def find_logical_port(self, search):
        ''' returns a match for a specific logical port '''
        logging.info("Looking for %s", search)
        for port in self.ports:
            if port.logical_name == search:
                return port
        # return false only if we didn't find a match
        return False

    def list_physical_ports(self):
        ''' returns a list of matching ports with physical interfaces '''
        # generator : returns matching objects rather than building a list then returning a list
        for port in self.ports:
            if port.physical_name:
                yield port

    def find_physical_port(self, search):
        ''' returns a matching port if found '''
        logging.info("Looking for %s", search)
        for port in self.ports:
            if port.physical_name == search:
                return port
        # return false only if we didn't find a match
        return False


###############
## FUNCTIONS ##
###############

def get_brcm_port_list(dev, switch):
    ''' splits and inverts list of two columns of data separated by newlines

        15.1X53-D30.5 - includes GOT: at the head of each line. includes an extra header row.
        17.1R3 - does not

        ['SENT:', 'Ukern', 'command:', 'show', 'dcbcm', 'ifd', 'all']
        ['GOT:']
        ['GOT:', '----------------------------------------------------------']
        ['GOT:', 'ifd', 'name', 'global-dev', 'local-dev', 'port-num', 'port-name']
        ['GOT:', '----------------------------------------------------------']
        ['GOT:', 'et-0/0/0', '0', '0', '50', 'ce12']
    '''

    port_list = dev.rpc.request_pfe_execute(target='fpc0', command='show dcbcm ifd all').text
    
    # split our output into lines
    port_list_lines = port_list.split("\n")

    # start parsing on 6th line
    for line in port_list_lines:
        # we're only interested in columns 0, 4 
        line_list = line.split()
        
        skip_headers = False

        if len(line_list) == 0:
            # skip blank lines
            continue

        if 'GOT:' in line_list[0]:
            # read at column one and two
            logical_name_column = 5
            physical_column = 1
            columns = 6
        else:
            # read at column zero and one
            logical_name_column = 4
            physical_column = 0
            columns = 5
        
        if len(line_list) == columns:
            logging.debug(line_list, logical_name_column, physical_column)
            
            # write "logical <tab> physical"
            logical_name = line_list[logical_name_column]
            physical_name = line_list[physical_column]

            # create a Port object
            port = Port(logical_name)
            port.physical_name = physical_name
            
            switch.add(port)


def get_brcm_pipe_map(dev, switch):
    ''' returns the PIPE to which the logical port is associated
        requires defaultdict as input to attach pipe information to using logical_port as key

        15.1X53-D30.5 - includes GOT: at the head of each line. includes an extra header row.
        17.1R3 - does not

        Expects: (missing column id for logical interface)
        'GOT:              pipe   logical  physical    mmu   ucast_Qbase/Numq  mcast_Qbase/Numq'
        'GOT:       ce28      3   118       113       200        80/10                80/10'
    '''

    pipe_map = dev.rpc.request_pfe_execute(target='fpc0', command='set dcbcm bc "show pmap"').text
    logging.info('Executing BRCM set dcbcm bc "show pmap"')
    # split output into lines
    pipe_map_lines = pipe_map.split("\n")
    logging.debug(pipe_map_lines)

    skip_headers = False

    # start parsing on 5th line
    for line in pipe_map_lines[5:]:
        # split into columns
        line_list = line.split()

        if len(line_list) == 0:
            # we found an empty line
            continue    # next line

        if 'GOT:' in line_list[0]:
            # read at column one and two
            logical_name_column = 1
            pipe_column = 2
            columns = 8
        else:
            # read at column zero and one
            logical_name_column = 0
            pipe_column = 1
            columns = 7

        if 'pipe' in line_list:
            skip_headers = True
            continue    # next line
        
        # we identified our header line earlier
        if skip_headers == True:    

            if len(line_list) == columns:
                logging.info(line_list)

                logical_name = line_list[logical_name_column]
                pipe = line_list[pipe_column]

                # we're only interested in columns 0, 1 (logical/pipe)
                # look up a matching port object
                port = switch.find_logical_port(logical_name)
                
                logging.debug(port)     # dump object contents
                
                if port:
                    logging.info("Adding %s to %s", (pipe, logical_name))
                    port.brcm_pipe = pipe
    

def get_brcm_drops(dev, switch):
    # takes a port_dict as input using logical_name as key and adds drop counters
    # these counters are only present during ingress congestion
    # DROP_PKT_ING.ce12	    :	      6,852,822,884	 +6,852,822,884
    # DROP_BYTE_ING.ce12	    :	    877,161,329,152    +877,161,329,152
    drop_output = dev.rpc.request_pfe_execute(target='fpc0',command= 'set dcbcm bc "show c"').text
    logging.info('Executing BRCM set dcbcm bc "show c"')
    # for each physical port check for drop counter
    for port in switch.list_physical_ports():
        
        logical_port = port.logical_name
        # should compile to resemble... "DROP_PKT_ING.*.ge1.*"
        # print "PERQ_PKT.*"+ logical_port + ".*"
        match_string = re.compile("DROP_PKT_ING.*"+ logical_port + ".*")
        # will return a [] of all matches for each logical_interface
        drops = match_string.search(drop_output)
        if drops:
            logging.info("DROP COUNTERS : %s", drops.group(0))
            # grab the raw drop counter by split on whitespace and pull 3rd column
            # ['DROP_PKT(7).xe24', ':', '315', '+1']
            total_drops = drops.group(0).split()[2]
            
            # append this counter to our port object
            port.brcm_drop_counter = total_drops

def print_table(switch, interface_table):
    ''' dumps collected data to screen '''
    print "Date&Time(PST):" + str(datetime.datetime.now())
    print "{:<15} {:<7} {:<8} {:<23} {:<10} {:<10} {:<8} {:<8} {:<13} {:<10} ".format('interface',
                                                                                      'logical',
                                                                                      'pipe',
                                                                                      'description',
                                                                                      'InBPS',
                                                                                      'OutBPS',
                                                                                      'InError',
                                                                                      'OutError',
                                                                                      'Admin/Oper',
                                                                                      'ingr_hw_drops')
    print('-' * 120)                                                                                  

    for item in interface_table:
        # look up the associated port object
        port = switch.find_physical_port(item.name)

        if port:
            # print only physical ports we can match
            logical_name = port.logical_name
            brcm_pipe = port.brcm_pipe
            brcm_drop_counter = port.brcm_drop_counter

            in_bps = convert_values(item.in_bps)
            out_bps = convert_values(item.out_bps)
            admin_oper = item.admin + "/" + item.oper

            # print out our data
            print("{:<15} {:<7} {:<8} {:<23} {:<10} {:<10} {:<8} {:<8} {:<13} {:<10}".format(item.name,
                                                                                                logical_name,
                                                                                                brcm_pipe,
                                                                                                item.description,
                                                                                                in_bps,
                                                                                                out_bps,
                                                                                                item.in_error,
                                                                                                item.out_error,
                                                                                                admin_oper,
                                                                                                brcm_drop_counter))


def convert_values(counter):
    ''' returns converted value in bps/mbps/gbps '''
    try:
        value = float(counter)
        if value >= 1000000000:
            return "{0:.2f}Gbps".format(value/1000000000)
        if value >= 1000000:
            return "{0:.2f}Mbps".format(value/1000000)
        elif value >= 1000:
            return "{0:.2f}Kbps".format(value/1000)
        else:
            return "{0:.2f}bps".format(value)
    except TypeError:
        return "----"


##########
## MAIN ##
##########

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", dest="host", help="target for connection", required=True)
    parser.add_argument("--user", dest="user", help="username to connect with", required=True)
    parser.add_argument("--interval", dest="interval", help="interval to poll the switch (s)", required=False)
    args = parser.parse_args()

    password = getpass.getpass()
    host = args.host
    if args.user:
        username = args.user
    else:
        sys.exit("Need username to continue...")

    # Change ERROR to INFO or DEBUG for more verbosity
    # Level	Numeric value
    # CRITICAL	50
    # ERROR	40
    # WARNING	30
    # INFO	20
    # DEBUG	10
    # NOTSET	0
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

    w = float(args.interval)

    # w = int(sys.argv[1])
    # # Python3 is input(), Python2 is raw_input()
    # try:
    #     input = raw_input
    # except:
    #     pass

    # open a connection to our device
    try:
        print ("Connecting to {0}...".format(host))
        dev = Device(host=host, user=username, passwd=password, port=22)
        dev.open()
    except ConnectError as err:
        logging.error("Cannot connect to device: %s", err)
        sys.exit(1)
    print "Connected!"
    
    # create an instance of our switch class
    switch = Switch()

    try:
        first_iteration = True

        while True:
            start_time = time.time()
            int_table_def = loadyaml('interface.yaml')
            int_table = int_table_def['InterfaceTable'](dev)
            # returns Name,Desc,in_bps,in,out,in_error,out_error,admin,oper
            int_table.get()

            # Format specifier for printing header and table items
            format_str = '%-12s  %-25s  %-10s %-10s  %-10s  %-10s  %-10s  %5s/%-5s'
            
          
            # only do these on first iteration since they don't change
            if first_iteration:
                # unset our flag
                first_iteration = False
                
                # create port list with physical & logical attributes
                get_brcm_port_list(dev, switch)
                # add pipe mapping
                get_brcm_pipe_map(dev, switch)
            
            # now do these on each loop

            # add drop counter
            get_brcm_drops(dev, switch)

            # for port in switch.ports:
            #     pp(vars(port))

            print_table(switch, int_table)
     
            print("--- %s seconds ---" % (time.time() - start_time))
            print "Sleeping for {}sec...".format(w)

            
            time.sleep(w)

    except KeyboardInterrupt:
        # if we still have a connection to our device, we should close it before we exit
        print "Caught Ctrl-C. Exiting!"
        if dev:
            dev.close()
        sys.exit()  # not exit with a 1 since we didn't error

# execute only if called directly (not as a module)
if __name__ == "__main__":

    # run our main program
    main()
