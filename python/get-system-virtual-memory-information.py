#!/usr/bin/python
#
# Simple script to collect tcp_inpcb info from SRX device(s) and report results
# in tabular format. Checks for buffer exhaustion and reports TRUE if within 10%
# of limit.
#
# barnesry-mbp:python barnesry$ ./get-system-virtual-memory-information.py --host 172.16.121.151 --user root
# Password:
# Checking for tcp_inpcb buffer issues...
# Host                	BufferLimit	CurrentUsage	AttnRequired?
# 172.16.121.151      	19964     	86          	False
#
# And here's what we're looking for
# barnesry@vsrx1_HUB> show system virtual-memory | display xml
#  <vmstat-memstat-zone>
# <zone-name>tcp_inpcb:</zone-name>
#             <zone-size>264</zone-size>
#             <count-limit>20640</count-limit>
#             <used>46</used>
#             <free>14</free>
#             <zone-req>50848</zone-req>
#  </vmstat-memstat-zone>
#

from jnpr.junos import Device
from lxml import etree
import argparse, logging, getpass, sys

threshold = 0.1     # 10% of buffer limit

def compare(limit, used, threshold):
    #determine if we have a sick router
    if used > (limit - (limit * threshold)):
        return True
    else:
        return False

def print_results(result_hash):
    # iterates through result_hash[host][mem_values]
    for key in result_hash:
        print("Checking for tcp_inpcb buffer issues...")
        print("{0:20}\t{1:10}\t{2:12}\t{3:20}".format('Host','BufferLimit','CurrentUsage','AttnRequired?'))
        print("{0:20}\t{1:10}\t{2:12}\t{3:}".format(key,
                result_hash[key]['count-limit'], result_hash[key]['used'],
                compare(int(result_hash[key]['count-limit']), int(result_hash[key]['used']), int(threshold) )))

def main(args):

    host = args.host
    user = args.user
    password = args.password
    result_hash = {}

    # setup our connection
    dev=Device(host=host, user=user, password=password)
    dev.open()

    # retrieve RPM results table in XML
    mem = dev.rpc.get_system_virtual_memory_information()

    # pull virtual memory data out of returned values
    result = mem.findall('.//vmstat-memstat-zone')

    # if our list isn't empty we found something worth reporting
    if result:

        found = 0
        iter = 0
        result_hash[host] = {}      # create a new entry for this device

        for index, item in enumerate(result[0]):

            if item.text.strip() == 'tcp_inpcb:':
                found = index   # set flag to something other than zero

            if found != 0 and iter <= 6:
                # Once we find tcp_inpcb, save next 6 items to hash
                result_hash[host][item.tag] = item.text.strip()
                logging.info("Index: {}, {}: {}".format(index,item.tag,item.text.strip()))
                iter += 1

        logging.info(result_hash[host])

    else:
        sys.exit("Coudn't find tcp_inpcb in 'rpc<get-system-virtual-memory-information>' request.")

    # Check our 'used' vs 'count-limit' ratio and report if we're within 10% of our limit
    print_results(result_hash)

# execute only if called directly (not as a module)
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
