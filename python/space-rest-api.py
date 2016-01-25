#! /usr/bin/python

import urllib
import urllib2
import ssl
import base64

url = "https://192.168.56.11/api/space"

authKey = base64.b64encode("super:juniper.space.r0cks")
headers = {"Content-Type":"application/json", "Authorization":"Basic " + authKey}
data = { "param":"value"}

gcontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
gcontext.verify_mode = ssl.CERT_REQUIRED
gcontext.check_hostname = False
gcontext.load_verify_locations('/Users/barnesry/Desktop/192.168.56.11.pem')

request = urllib2.Request(url)

# post form data
# request.add_data(urllib.urlencode(data))

for key,value in headers.items():
  request.add_header(key,value)

response = urllib2.urlopen(request, context=gcontext)

print response.info().headers
print response.read()
