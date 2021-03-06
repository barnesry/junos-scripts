#! /usr/bin/python

# Retreive arbitrary information from remote devices using NETCONF RPC calls


import sys
import argparse

from jnpr.junos.utils.config import Config
from jnpr.junos.exception import *
from jnpr.junos import Device
from pprint import pprint as pp
from lxml import etree

def getArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--target", dest="target", help="ip_address to connect to", required=True)
    parser.add_argument("-u", "--user", dest="user", help="username to connect", required=True)
    parser.add_argument("-p", "--password", dest="password", help="password to connect", required=True)
    parser.add_argument("-c", "--command", dest="rpcCommand", help="rpc request to send to target in quotes", required=True)
    return parser.parse_args()
    #pp(args.target)

def connectDevice(dev):
    print("Attempting to open a connection to {0}...".format(dev.hostname)),
    try:
        dev.open()
        print "Success!"
    except Exception as err:
        print "Cannot connect to device:", err

def lockConfig(dev):
    print "Locking the configuration...",
    try:
        dev.cu.lock()
        print "Success!"
    except LockError:
        print "Error: Unable to lock configuration"
        dev.close()

def unlockConfig(dev):
    print "Unlocking the configuration...",
    try:
        dev.cu.unlock()
        print "Success!"
    except UnlockError:
        print "Error: Unable to unlock configuration"
    dev.close()

def loadConfig(dev, configfile):
    print "Loading configuration changes...",
    try:
        dev.cu.load(path=configfile, merge=True)
        print "Success!"
    except ValueError as err:
        print "Uh Oh, something went wrong.", err.message

    except Exception as err:
        if err.cmd.find('.//ok') is None:
            rpc_msg = err.rsp.findtext('.//error-message')
            print "Unable to load configuration changes: ", rpc_msg

            # since we failed to apply the config we need to unlock it
            unlockConfig(dev)


def main():

    usage = "Usage: %prog -t <target_IP> -u <username> -p <password>"

    # get our args from the commandline
    args = getArguments()

    # construct our Device object
    dev = Device(user=args.user, host=args.target, password=args.password)

    # Open a connection
    connectDevice(dev)

    # Bind Config instance to Device instance
    # dev.bind( cu=Config )

    # Lock the configuration
    # lockConfig(dev)

    # Check our diffs
    #print "Displaying Diffs..."
    #dev.cu.pdiff()

    #invoke the RPC equivalent to "show version"
    sw = dev.rpc.get_software_information()
    print(etree.tostring(sw))

    # get interface info
    #interfaces = dev.rpc.get_interface_information(terse=True)

    # get license info
    license = dev.rpc.get_license_summary_information()

    licese_key = dev.rpc.get_license_key_information()

    print(etree.tostring(license))
    print(etree.tostring(licese_key))
    # will save a rescue config, but complain about it
    # result = dev.cli(command="request system configuration rescue save")

    # unlock the config
    # unlockConfig(dev)

# executes only if not called as a module
if __name__ == "__main__":
   main()
