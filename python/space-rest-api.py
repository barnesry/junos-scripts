#! /usr/bin/python
#
# Test script to connect to the Juniper Space REST API and return some basic info
#

import urllib
import urllib2
import requests
import ssl
import base64
from lxml import etree
from xml.sax.saxutils import unescape

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


###############
## FUNCTIONS ##
###############

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

def listDevices(host, context):
    url = "https://"+host+"/api/space/device-management/devices"

    devicelist = submitRestRequest(url, authKey, context)

    # read in the response body
    xml = devicelist.read()
    # load the xml into the parser

    tree = etree.fromstring(xml)

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

    for device in devices:
        device.show()

    #return xml  # in the event we want to do something else with this data
    return devices


def sendRpc(host, device, rpc_command):

    command = rpc_command
    headers = {"Content-Type":"application/vnd.net.juniper.space.device-management.rpc+xml;version=1;charset=UTF-8",
                "Authorization":"Basic " + authKey}
    #data = { "param":"value"}
    data = '<netconf><rpcCommands><rpcCommand><![CDATA[<get-system-information/>]]></rpcCommand></rpcCommands></netconf>'
    queue_url = 'https://192.168.56.11/api/hornet-q/queues/jms.queue.testq'
    url = "https://"+host+"/api/space/device-management/devices/"+device.id+"/exec-rpc?queue-url="+queue_url

    try:
        r = requests.post(url, data=data, headers=headers, auth=('super', 'juniper.space.r0cks'), verify=False)
    except:
        print("error!")
        r.status.code

    if not r.raise_for_status:
        print r.status_code
        print r.headers
        print r.text

    # massage our output to standard XML reply
    xml = unescape(r.text, { "&quot;" : '"'}).replace('\n', '')

    #print xml
    # still had some unicode stuff that needed escaping to parse xml
    clean_xml = xml.decode('unicode_escape').encode('ascii','ignore')

    # load into the xml parser
    tree = etree.fromstring(clean_xml)

    print tree.find('.//replyMsgData').tag

    # dump all our attributes we retrieved
    for child in tree.iter():
        print("{:20} : {}".format(child.tag, child.text))


def createQueue(host, authKey, context):

    headers = {"Content-Type":"application/hornetq.jms.queue+xml"}
    payload = '<queue name="testq26"><durable>false</durable></queue>'

    url = 'https://'+host+'/api/hornet-q/queues'

    try:
        r = requests.post(url, data=payload, headers=headers, auth=('super', 'juniper.space.r0cks'), verify=False)
    except:
        print "error!"

    if not r.raise_for_status():    # did we create the queue successfully?
        location = r.headers['Location']

        # why not
        print r.status_code
        print r.headers
        print r.text

    return location     # this is the URI of the hornet-q we need to check



#################
## MAIN BLOCK  ##
#################
def main():
    #url = "https://"+host+"/api/space"

    # dump a list of devices to the screen and return an xml fragment
    devicelist = listDevices(host, gcontext)

    # Dump our response
    #print devicelist.info().headers
    #print devicelist.read()

    #sendRpc(host,devicelist[0], 'get-system-information')

    # location = createQueue(host,authKey, gcontext)
    #print location

    result = sendRpc(host, devicelist[0], 'get-system-information')

# executes only if not called as a module
if __name__ == "__main__":
   main()
