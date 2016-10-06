from libsoundannotator.streamboard.network import NetworkMixin
from libsoundannotator.streamboard.subscription import NetworkConnection
import time, numpy as np, sys, cPickle

config = {
	'interface': sys.argv[2],
	'port': 1060
}

class DataObject(object):
	def __init__(self, n, data, metadata):
		self.n = n
		self.data = data
		self.metadata = metadata

class ServerTest(NetworkMixin):

	def __init__(self, config, *args, **kwargs):
		serverconf = config
		serverconf['type'] = 'server'
		self.connection = NetworkConnection(serverconf)

	def printData(self, data):
		print data.metadata

	def run(self):
		print "Running server"
		while True:
			new = self.connection.poll()
			if new:
				data = self.connection.recv()
				if data:
					print "Got package {0}".format(data.n)
			time.sleep(0.025)

class ClientTest(NetworkMixin):
	
	def __init__(self, config, *args, **kwargs):
		clientconf = config
		clientconf['type'] = 'client'
		self.connection = NetworkConnection(clientconf, pollTimeout=2.0)

	def run(self):
		print "Running client"
		n = 1
		data = np.random.randint(1, 150, size=22050)
		metadata = {
				'description': 'Test for client :)'
		}
		package = DataObject(n, data, metadata)
		while True:
				package.n += 1
				print "Send package {0}".format(package.n)
				try:
						self.connection.send(package)
				except:
						pass
				time.sleep(0.5)



if sys.argv[1] == 'server':
	config['type'] = 'server'
	st = ServerTest(config)
	st.run()
elif sys.argv[1] == 'client':
	config['type'] = 'client'
	st = ClientTest(config)
	st.run()
