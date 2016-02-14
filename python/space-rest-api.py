#! /usr/bin/python
#
# Test script to connect to the Juniper Space REST API and return some basic info
#

import urllib
import urllib2
import requests
import argparse
import ssl
import base64
import sys
from lxml import etree
from xml.sax.saxutils import unescape
from pprint import pprint as pp

# we can override this with the -d flag at the commandline
debug = False

host = '192.168.56.11'
authKey = base64.b64encode("super:juniper.space.r0cks")

# Build SSL context to load self-signed CA certificate from Space
gcontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
gcontext.verify_mode = ssl.CERT_REQUIRED
gcontext.check_hostname = True
gcontext.load_verify_locations('/Users/barnesry/Desktop/192.168.56.11.pem')


#############
## CLASSES ##
#############
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


class Space:
    def __init__(self, host, authKey, context):
        self.host = host
        self.authKey = authKey
        self.context = context

    def describe(self):
        print("Connection parameters :\n\tTarget : {}".format(self.host))

    def get_device_list(self):

        url = "https://"+self.host+"/api/space/device-management/devices"

        response = submitRestRequest(url, self.authKey, self.context)


        tree = self.http_to_xml(response)

        # we'll return a list of python objects
        devices = []

        # print some headers
        print("{:10}{:10}{:10}".format('ID', 'Name', 'IP_Address'))

        # now parse our devices xml to extract interesting bits
        for device in tree:
            uri = device.attrib.get('uri')
            id = device.get('key')
            name = device.find('.//name').text
            ipaddr = device.find('.//ipAddr').text
            serialnumber = device.find('.//serialNumber').text
            platform = device.find('.//platform').text

            devices.append(Device(id,uri,name,ipaddr,serialnumber,platform))

            print("{:10}{:10}{:10}".format(id, name, ipaddr))

        if debug:
            for device in devices:
                device.show()

        #return xml  # in the event we want to do something else with this data
        return devices

    def createQueue(self, queue_name):

        headers = {"Content-Type":"application/hornetq.jms.queue+xml"}
        payload = '<queue name="'+queue_name+'"><durable>false</durable></queue>'
        queue_url = ''
        url = 'https://'+self.host+'/api/hornet-q/queues'

        if debug:
            print("Calling {} with a payload of \n {}".format(url,payload))

        try:
            r = requests.post(url, data=payload, headers=headers, auth=('super', 'juniper.space.r0cks'), verify=False)
        except requests.ConnectionError, err:
            print("{} : Could not connect to host".format(err))
            sys.exit(1)

        if r.status_code == 412:    # error we get if the queue exists already
            print(r.text)
            queue_url = 'https://'+self.host+'/api/hornet-q/queues/jms.queue.'+queue_name
        elif r.status_code == 201:  # success
            queue_url = r.headers['Location']    # grab the Location header
        elif r.raise_for_status():    # should report True if we got a 2xx response
            print("Uh Oh. Unexpected HTTP Return code : {}".format(r.status_code))
            sys.exit(1)

        return queue_url     # this is the URI of the hornet-q we need to check

    def createQueueConsumer(self, queue):
        url = 'http://'+self.host+'/api/hornet-q/queues/jms.queue.'+queue+'/pull-consumers'
        print("QueueConsumerRequest : {}".format(url))



    def http_to_xml(self, response):
        # read in the response body
        xml = response.read()
        # load the xml into the parser
        tree = etree.fromstring(xml)

        return tree

###############
## FUNCTIONS ##
###############

def help():
    print('''
    Usage : Send RPC Command for target device via Space REST API.

    Example: space-rest-api.py -c get-license-summary-information

    ''')


def submitRestRequest(url, authkey, context):

    headers = {"Content-Type":"application/json", "Authorization":"Basic " + authKey}
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
    response = urllib2.urlopen(request, context=gcontext)

    return response



def sendRpc(host, device, rpc_command):

    command = rpc_command
    headers = {"Content-Type":"application/vnd.net.juniper.space.device-management.rpc+xml;version=1;charset=UTF-8",
                "Authorization":"Basic " + authKey}
    #data = { "param":"value"}
    data = '<netconf><rpcCommands><rpcCommand><![CDATA[<'+command+'/>]]></rpcCommand></rpcCommands></netconf>'

    queue_url = 'https://192.168.56.11/api/hornet-q/queues/jms.queue.testq'
    url = "https://"+host+"/api/space/device-management/devices/"+device.id+"/exec-rpc?queue-url="+queue_url

    if debug:
        print("Requesting URL : {}".format(url))
        print("URL Data : {}".format(data))

    try:
        r = requests.post(url, data=data, headers=headers, auth=('super', 'juniper.space.r0cks'), verify=False)
    except:
        print("error!")
        r.status.code

    if not r.raise_for_status:
        print r.status_code
        print r.headers
        print r.text

    if debug:
        print("Response Body : {}".format(r.text))

    # massage our output to standard XML reply
    xml = unescape(r.text, { "&quot;" : '"'}).replace('\n', '')

    #print xml
    # still had some unicode stuff that needed escaping to parse xml
    clean_xml = xml.decode('unicode_escape').encode('ascii','ignore')

    # load into the xml parser
    tree = etree.fromstring(clean_xml)

    # check for success of our command
    status = tree.find('.//status').text

    if status == 'Failure':
        print("Command returned : {}".format(status))
        sys.exit(1)
    #print tree.find('.//replyMsgData')

    # dump all our attributes we retrieved
    for child in tree.iter():
        print("{:20} : {}".format(child.tag, child.text))

def sendRpc_new(host, headers, payload, url, queue_url):

    if debug:
        print("Requesting URL : {}".format(url))
        print("URL Data : {}".format(payload))

    try:
        r = requests.post(url, data=payload, headers=headers, auth=('super', 'juniper.space.r0cks'), verify=False)
    except:
        print("error!")
        r.status.code

    if not r.raise_for_status:
        print r.status_code
        print r.headers
        print r.text

    if debug:
        print("Status Code : {}".format(r.status_code))
        print("Headers : {}".format(r.headers))
        if r.text is not None:
            print("Response Body : {}".format(r.text))


    #clean_xml = cleanXML(r.text)

    #print(clean_xml)
    sys.exit(1)

    # load into the xml parser
    tree = etree.fromstring(clean_xml)

    # check for success of our command
    status = tree.find('.//status').text

    if status == 'Failure':
        print("Command returned : {}".format(status))
        sys.exit(1)
    #print tree.find('.//replyMsgData')

    # dump all our attributes we retrieved
    for child in tree.iter():
        print("{:20} : {}".format(child.tag, child.text))




def getSyslogEvents(host, device):

    queue_url = "https://"+host+"/api/hornet-q/queues/jms.queue.testq"
    url = "https://"+host+"/api/space/device-management/devices/get-syslog-events?queue-url="+queue_url
    headers = {"Content-Type":"application/vnd.net.juniper.space.device-management.get-syslog-events+xml;version=2;charset=UTF-8",
                "Authorization":"Basic " + authKey}
    payload = "<get-syslog-events>                                                          \
                    <devices>                                                               \
                        <device href=\"/api/space/device-management/devices/"+device.id+"\"/> \
                    </devices>                                                                \
                  <text-patterns>                                                           \
                    <text-pattern>LICENSE</text-pattern>                                    \
                  </text-patterns>                                                          \
                </get-syslog-events>"


    sendRpc_new(host, headers, payload, url, queue_url)

def cleanXML(xml):

    # massage our output to standard XML reply
    xml = unescape(xml, { "&quot;" : '"'}).replace('\n', '')

    # still had some unicode stuff that needed escaping to parse xml
    clean_xml = xml.decode('unicode_escape').encode('ascii','ignore')

    return clean_xml

#################
## MAIN BLOCK  ##
#################
def main(args):

    # retreive our Arguments
    args = args
    command = args.rpcCommand

    # set debug flag if we've specified -d at the commandline
    if args.debug:
        global debug
        debug = True


    instance = Space(host, authKey, gcontext)

    instance.get_device_list()

    # create our queue
    queue = instance.createQueue('testq47')
    print("Queue Location : {}".format(queue))

    sys.exit(0)

    #sendRpc(host,devicelist[0], 'get-system-information')

    # location = createQueue(host,authKey, gcontext)
    #print location

    #result = sendRpc(host, devicelist[1], command)
    #queue = createQueue(host, authKey, gcontext)
    result = getSyslogEvents(host, devicelist[1])

# executes only if not called as a module
if __name__ == "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument("-c", "--command", dest="rpcCommand", help="rpc request to send to target in quotes", required=True)
   parser.add_argument("-d", "--debug", help="sets additional verbosity", action="store_true")
   args = parser.parse_args()

   main(args)
