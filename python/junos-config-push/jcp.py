#!/usr/env/python3

''' This script uses the local /etc/hosts file on MacOS to execute RPC calls based on wildcard
    inputs
    
    # example targets labrouter-r1 and labrouter-r2 to return arbitary command
    python3 jcp.py --target labrouter-r[12] --user root --password Password1 --command "show pfe statistics traffic"

    # config example
    # opens a local configlet, and pushes to target with diff and commit/confirm
    python3 jcp.py --target labrouter-r[12] --user root --password Password1 --config test.j2

'''

import os
import re
import argparse
import logging
import time
from pprint import pprint
from lxml import etree
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import ConnectAuthError, LockError, ConfigLoadError, UnlockError, \
                                    CommitError, RpcError, ConnectTimeoutError

debug = False
commit_confirm_time = 1
commit_confirm_percentage = 0.8

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

def read_config_file(filename):
    ''' Opens the target file and returns the contents '''
    try:
        if debug:
            logging.info("Opening {}".format(filename))

        with open(filename, 'r') as f:
            config = f.read()
            return config
    
    except FileNotFoundError:
        print("Can't open ConfigFile : {}".format(filename))

def should_we_continue():
    response = input("Proceed? [y/N] : ")
    if response == "\n":
        return False
    elif response.upper() == "N":
        return False
    elif response.upper() == "Y":
        return True
    else:
        return False

def commit_wait_time(commit_confirm_time = commit_confirm_time,
                     commit_confirm_percentage = commit_confirm_percentage):
    ''' Returns int(num_seconds) as a percentage of total commit_confirm time
        eg. percentage expressed as 0.8, not 80% 
    '''

    return int(commit_confirm_time * 60 * commit_confirm_percentage)

def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', required=True, dest='target', help='Target host(s) to connect to based on regex')
    parser.add_argument('--user', required=True, dest='user', help='username to connect with')
    parser.add_argument('--password', required=True, dest='password', help='password for target host')
    parser.add_argument('--command', required=False, dest='command', help='command to execute on host')
    parser.add_argument('--config', required=False, dest='config', help='configlet to push to host')
    parser
    args = parser.parse_args()
    target = args.target
    user = args.user
    password = args.password
    if args.command:
        command = args.command
    else:
        command = ''
    if args.config:
        configfile = args.config
    else:
        configfile = ''


    for hostname in read_hosts():
        # for anything matching our regex provided at the cli
        if re.match(target, hostname):
            
            try:
                dev = Device(host=hostname, user=user, password=password, timeout=30)
                logging.warning("Connecting : {}".format(dev.hostname))
                dev.open()

                # check which action we want to take based on args
                if command:
                    # we want to run a show command
                    result = dev.rpc.cli(command)
                    
                    get_output = etree.XPath("//output/text()")
                    # extract text from root <output> node
                    output = get_output(result)[0]
                    
                    print(f'{hostname} : {output}')
                    
                elif configfile:
                    # we want to push some config
                    config = read_config_file(configfile)[0]
                    
                    cu = Config(dev)
                    try: 
                        logging.warning("Locking configuration...")
                        cu.lock()
                    except LockError as err:
                        print("FAIL : Unable to lock configuration : {}".format(err))
                        return

                    try:
                        logging.warning("Loading configlet...")
                        cu.load(config, format="text")
                    except ConfigLoadError as err:
                        print("FAIL : Unable to load config: {}".format(err))
                        cu.unlock()
                        return

                    # show the diff
                    print(f'{dev.hostname} : DIFF')
                    print(f'{"#"*20}')
                    cu.pdiff()
                    
                    # wait for user to confirm it's OK to proceed after viewing diff
                    if should_we_continue() is False:
                        logging.warning("Attempting rollback...")
                        rollback_result = cu.rollback()
                        if rollback_result:
                            logging.warning("Rollback SUCCESS")
                        else:
                            logging.warning("Rollback FAILED")

                        try :
                            logging.warning("Unlocking Config")
                            cu.unlock()
                        except:
                            logging.warning("Unlock FAILED")

                    # else assume we recieved the OK to proceed
                    else:
                        try:
                            logging.warning("COMMIT Confirmed={}...".format(commit_confirm_time))
                            cu.commit(confirm=commit_confirm_time, comment="COMMIT by jcs.py")
                            
                            logging.warning("Waiting for {} seconds before second commit attempt".format(
                                            commit_wait_time()))
                            time.sleep(commit_wait_time())
                            cu.commit(comment="COMMIT CONFIRMED by jcs.py")
                            logging.warning("SUCCESS : Commit")

                            try:
                                logging.warning("SUCCESS : Unlocking Config")
                                cu.unlock()
                            except UnlockError:
                                logging.error("FAIL : Could not unlock config")
                                return
                        except CommitError as err:
                            logging.error("FAIL : Could not commit : {}".format(err))
                            return
                            

                        except CommitError as err:
                            print("FAIL : Could not commit : {}".format(err))
                            cu.rollback()
                            cu.unlock()
                            return  
                        except RpcError as err:
                            print("FAIL : ncclient issues : {}".format(err))
                            cu.rollback()
                            cu.unlock()
                            return
                
                logging.warning("CLOSING Connection : {}".format(hostname))
                dev.close()
            
            except ConnectAuthError as f:
                logging.error(" %s" % f)
                new_auth = get_username_and_password()
                user = new_auth['user']
                password = new_auth['password']
                dev = Device(host=target, user=user, password=password)
                logging.warning("Connecting to {}".format(dev.hostname))
                dev.open()
            except ConnectTimeoutError as err:
                logging.error("FAIL to connect to {} : {}".format(dev.hostname, err))
                continue


if __name__ == "__main__":
    
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
    
    main()
