from jnpr.junos.device import Device
from myPyezTables.bgpNeighborTable import BgpNeighborTable
from jnpr.junos.exception import *
from pprint import pprint
from getpass import getpass

# $ python3 myPyez_bgp_neighbor_by_ri.py
# Username: labuser
# Password:
# IP or Hostname : lab-router-1
# ROUTING-INSTANCE        PEER-IP           PEER-STATE
# ---------------------------------------------------------------------------
# VPN-1.inet.0            10.254.1.254     Established
# VPN-2.inet.0            10.254.2.254     Established


def main():

    # get username/password/target
    username = input("Username: ")
    password = getpass()
    target = input("IP or Hostname : ")

    dev = Device(host = target, user = username, password = password, timeout = 10)
    try:
        dev.open()
        bgpSummary = BgpNeighborTable(dev)  # attach table to device
        peers = bgpSummary.get()

        print(f'{"ROUTING-INSTANCE":35s}{"PEER-IP":18s}{"PEER-STATE":20s}')
        print("-"*75)

        for item in peers:
            print(f'{item.rib:35s}{item.peerip:18s}{item.peerstate:20s}')

        dev.close()
    except ConnectTimeoutError as e:
        print("The connection timed out.")

if __name__ == "__main__":
    main()