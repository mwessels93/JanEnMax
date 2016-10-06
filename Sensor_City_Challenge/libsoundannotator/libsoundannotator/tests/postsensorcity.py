import xml.etree.ElementTree as ET, urllib2 as urllib, time
import numpy as np
node_id = '337'
url = 'http://sensorcity.casper.aero/collector'
values = (np.random.rand(4)*20).astype(int)
def formattime():
	return "{0:.0f}".format(time.time())

root = ET.parse('template_update.xml').getroot()
root.set('time', formattime())
noise = ET.SubElement(root, 'noise')
noise.set('nmt_id', node_id)
noise.set('time', formattime())

noise.set('pulse', str(values[0]))
noise.set('tone', str(values[1]))
noise.set('noise', str(values[2]))
noise.set('dB', str(values[3]))

xmlstr = ET.tostring(root, encoding='UTF-8')

print xmlstr

req = urllib.Request(url=url,
	data=xmlstr,
	headers={'Content-Type':'application/xml'})

resp = urllib.urlopen(req)

print resp.getcode()
print resp.info()
print resp.read()