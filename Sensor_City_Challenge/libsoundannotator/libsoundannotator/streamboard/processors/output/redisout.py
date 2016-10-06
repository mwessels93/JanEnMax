from libsoundannotator.streamboard				import processor
from libsoundannotator.streamboard.continuity 	import Continuity

import redis, os, time
import numpy as np

'''
	Processor that connects to a Redis instance and publishes data there
'''
class RedisWriter(processor.Processor):

	requiredKeys=['redisdata']

	'''
		Required parameters are:

		- RedisHost: the host to connect to
		- RedisPort: the corresponding port
	'''
	def __init__(self, conn, name, *args, **kwargs):
		super(RedisWriter, self).__init__(conn, name, *args, **kwargs)
		self.requiredParameters('TTL', 'TTR')
		self.requiredParametersWithDefault(RedisHost='localhost', RedisPort=6379)

	def prerun(self):
		self.redis = redis.StrictRedis(host=self.config['RedisHost'], port=self.config['RedisPort'])
		super(RedisWriter, self).prerun()

	'''
		The storage convention:
		We let Redis expose a list, 'availablefiles', that contains files for which we have data.
		A client may choose to visualise the data from one of those files, so it must be accessible.
		The data itself is stored in an ordered list per file, that contains data for
		the last TTL chunks.
		The naming of this list is 'filename_data' with filename being the name of the file
	'''
	def processData(self, chunk):
		key = chunk.received['redisdata']
		data = key.data
		ID = chunk.identifier
		self.logger.info("Received redis data with ID {0}".format(ID))
		#add the file to the set if not yet available
		if not self.redis.sismember('availablefiles', ID):
			self.redis.sadd('availablefiles', ID)

		#set online key
		self.redis.set('{0}:online'.format(ID), 1)
		self.redis.expire('{0}:online'.format(ID), 1)

		#set available key to expire after last entry
		self.redis.set('available:{0}'.format(ID), 1)
		self.redis.expire('available:{0}'.format(ID), self.config['TTR'])

		#flatten the data column-wise (because the amount of rows is always given)
		storedata = ','.join([str(i) for i in data.astype(np.int).flatten('F')])
		#add the data to the sorted list
		self.redis.lpush("buffer:{0}".format(ID), storedata)

		self.redis.expire("buffer:{0}".format(ID), self.config['TTR'])

		#remove old data from the list (older than 60 sec)
		self.redis.ltrim("buffer:{0}".format(ID), 0, self.config['TTL'] - 1)
		
		self.redis.publish('pub:{0}'.format(ID), storedata)

		#return the data to be able to hook more processors after this one
		return {
			'redisdata' : storedata
		}

	def finalize(self):
		if hasattr(self, 'redis'):
			self.redis.client_kill();
