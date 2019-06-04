#!/usr/env/python3

''' This script uses the local /etc/hosts file on MacOS to execute RPC calls based on wildcard
    inputs
    
    # example targets labrouter-r1 and labrouter-r2 to return arbitary command
    python3 jcp.py --target labrouter-r[12] --user root --password Password1 --command "show pfe statistics traffic"

'''

import os
import re
import argparse
import logging
import io
from pprint import pprint
from lxml import etree
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import ConnectAuthError

debug = False

host_file = '/etc/hosts'
host_list = []

def read_hosts():
    # read local hosts file and return all hostnames as a single python list
    try: 
        print(f"Opening {host_file}")
        with open(host_file, 'r') as f:
            
            for line in f.readlines():
                # only return actual host entries not all the other stuff
                if re.match("^[0-9]", line):
                    var1 = line.split()
                    # drop the first ip column
                    for hostname in var1[1:]:
                        host_list.append(hostname)
            
        return host_list
    
    except FileNotFoundError:
        print("File not Found")

def get_username_and_password():
    ''' Get username and password from user '''
    auth = {}
    print("Username: ")
    auth['user'] = input()
    print("Password: ")
    auth['password'] = input()

    return dict(auth)

    
def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', required=True, dest='target', help='Target host(s) to connect to based on regex')
    parser.add_argument('--user', required=True, dest='user', help='username to connect with')
    parser.add_argument('--password', required=True, dest='password', help='password for target host')
    parser.add_argument('--command', required=False, dest='command', help='command to execute on host')
    args = parser.parse_args()
    target = args.target
    user = args.user
    password = args.password
    if args.command:
        command = args.command
    else:
        command = ''


    for hostname in read_hosts():
        if re.match(target, hostname):
            
            try:
                dev = Device(host=hostname, user=user, password=password)
                logging.warning("Connecting to {}".format(dev.hostname))
                dev.open()

                if command:
                    result = dev.rpc.cli(command)
                    
                    get_output = etree.XPath("//text()")
                    # extract text from root <output> node
                    output = get_output(result)[0]
                    print(f'{hostname} : {output}')
                    
                else:
                    pprint(dev.facts)

                dev.close()
            except ConnectAuthError as f:
                logging.error(" %s" % f)
                new_auth = get_username_and_password()
                user = new_auth['user']
                password = new_auth['password']
                dev = Device(host=target, user=user, password=password)
                logging.warning("Connecting to {}".format(dev.hostname))
                dev.open()




if __name__ == "__main__":
    
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
    
    main()
