#! /usr/bin/python
#
# Author        : barnesry@juniper.net
# Date          : September 6, 2017
# Description   : Pulls AWS Public IP Blocks and returns a simple list 
#                 for consumption by Security Director PE
#
# 
# 
##

import urllib, urllib2, requests, argparse, ssl, base64
import json
import sys, logging
from pprint import pprint as pp

aws_url = 'https://ip-ranges.amazonaws.com/ip-ranges.json'

###############
## FUNCTIONS ##
###############
def submitRestRequest(url):
    headers = {"Content-Type":"application/text"}
    data = { "param":"value"}

    # build the request so we can add auth headers later
    request = urllib2.Request(url)

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    # post form data
    # request.add_data(urllib.urlencode(data))

    # # add our auth headers
    # for key,value in headers.items():
    #   request.add_header(key,value)

    # Open the URL passing the newly built request object, passing SSL context to
    # to modify it's connection behavior
    response = urllib2.urlopen(request, context=context)

    return response

def parse_v4(json_body):
    
    ip_list = []
    parsed_json = json.loads(json_body)

    for prefix in parsed_json['prefixes']:
        ip_list.append(prefix['ip_prefix'])

    return ip_list

################
## MAIN BLOCK ##
################
def main():

    try:
        response = submitRestRequest(aws_url)
    except urllib2.HTTPError as e:
        print e.code
        print e.read()
        
    # print response.read()

    ip_list = parse_v4(response.read())

    print '\n'.join(ip_list)


# execute only if called directly (not as a module)
if __name__ == "__main__":

    # run our main program
    main()