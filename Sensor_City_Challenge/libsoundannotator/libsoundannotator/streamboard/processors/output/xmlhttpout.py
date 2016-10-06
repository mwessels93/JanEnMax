from libsoundannotator.streamboard				import processor
from libsoundannotator.streamboard.continuity 	import Continuity
import os, urllib2 as urllib, time, numpy as np

import xml.etree.ElementTree as ET

'''
	Processor that performs an HTTP POST of PTNE data to a specific URL for the SensorCity project
'''
class SensoryCityXmlOutputProcessor(processor.OutputProcessor):
	lookup = {
		'P': 'pulse',
		'N': 'noise',
		'T': 'tone',
		'E': 'dB'
	}
	valuetypes = ['percent', 'default']
	def __init__(self, conn, name, *args, **kwargs):
		super(SensoryCityXmlOutputProcessor, self).__init__(conn, name, *args, **kwargs)
		self.requiredKeys = kwargs.get('requiredKeys', self.requiredKeys)
		''' Required parameters are:
			- The URL of the endpoint to connect to
			- The XML template to POST when adding a new node
			- The XML template to POST when upating a node
		'''
		self.requiredParameters('URL', 'id', 'accumulate')
		self.requiredParametersWithDefault(valuetype='percent')

	def prerun(self):
		super(SensoryCityXmlOutputProcessor, self).prerun()
		#load the templates as elementtree
		self.xmlUpdate = ET.parse('template_update.xml')
		self.xmlroot = self.xmlUpdate.getroot()

		if not self.config['valuetype'] in self.valuetypes:
			raise Exception('Given value type is unknown: {0}'.format(self.config['valuetype']))

	def processData(self, smartChunk):
		#put the values in a noise element
		noise = ET.SubElement(self.xmlroot, 'noise')
		noise.set('time', "{0:.0f}".format(time.time()))
		noise.set('nmt_id', self.config['id'])

		received = smartChunk.received

		for key in received:
			if not key in self.lookup:
				raise Exception('Got unknown key {0}. Lookup: {1}'.format(key, str(self.lookup)))

			data = received[key].data[0]
			self.logger.info(','.join("{0:.2f}".format(num) for num in data))
			datastr = ','.join("{0:.2f}".format(num) for num in data)
			noise.set(self.lookup[key], datastr)


		if len(self.xmlroot.getchildren()) == self.config['accumulate']:
			self.post()
			for child in self.xmlroot.findall('.//noise'):
				self.xmlroot.remove(child)

	def post(self):
		self.xmlroot.set('time',"{0:.0f}".format(time.time()))
		xmlstr = ET.tostring(self.xmlroot, encoding='UTF-8')
		self.logger.info("POST string to {0}:\n{1}".format(self.config['URL'], xmlstr))

		req = urllib.Request(url=self.config['URL'],
			data=xmlstr,
			headers={'Content-Type':'application/xml'})
		resp = urllib.urlopen(req)
		self.logger.info("Statuscode {0}".format(resp.getcode()))
		self.logger.info("Message: {0}".format(resp.read()))
		
