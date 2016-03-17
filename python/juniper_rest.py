#! /usr/bin/python
#
# Author        : barnesry@juniper.net
# Date          : March 7, 2016
# Description   :
#
#
##

import urllib, urllib2, requests, argparse, ssl, base64
import sys, logging
from pprint import pprint as pp


#############
## CLASSES ##
#############
class RestConnect:
    def __init__(self, host, port=8110):
        self.host = host
        self.port = port

    def describe(self):
        print("Connection Parameters : \n \
        Target : {0} \n \
        Port : {1}".format(self.host, self.port))

    def connect(self):
        url = print("http://{}:{}/rpc?exit-on-error=1".format(
            self.host, self.port))
        print url

    def get_facts(self):
        # connect to device and retrieve stuff
        pass


class Device:
    def __init__(self, id, uri, name, ipaddr, serialnumber, platform):
        self.id = id
        self.uri = uri
        self.name = name
        self.ipaddr = ipaddr
        self.serialnumber = serialnumber
        self.platform = platform

    def show(self):
        print(self.name)
        print("  ID : {}".format(self.id))
        print("  IP : {}".format(self.ipaddr))
        print("  Serial: {}".format(self.serialnumber))


def submitRestRequest(url):
    headers = {"Content-Type":"application/text"}
    data = { "param":"value"}

    # build the request so we can add auth headers later
    request = urllib2.Request(url)

    # post form data
    # request.add_data(urllib.urlencode(data))

    # add our auth headers
    for key,value in headers.items():
      request.add_header(key,value)

    # Open the URL passing the newly built request object, passing SSL context to
    # to modify it's connection behavior
    response = urllib2.urlopen(request)

    return response

################
## MAIN BLOCK ##
################
def main(args):

    connection = RestConnect(host=args.host)

    connection.describe()

    connection.connect()


# execute only if called directly (not as a module)
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", dest="host", help="target for REST call", required=True)
    args = parser.parse_args()

    # run our main program
    main(args)
