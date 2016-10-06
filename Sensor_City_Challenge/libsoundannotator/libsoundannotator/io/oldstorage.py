import json, os, sys, time

class StorageFormatter(object):

	def __init__(self, *args, **kwargs):
		pass

	def format(self, data):
		raise Exception("Implement this in subclass")

class XmlStorage(StorageFormatter):

	def __init__(self, *args, **kwargs):
		super(XmlStorage, self).__init__(*args, **kwargs)

		self.foldername = 'xml'

	def format(self, data):
		pass

class JsonStorage(StorageFormatter):

	def __init__(self, *args, **kwargs):
		super(JsonStorage, self).__init__(*args, **kwargs)

		self.foldername = 'json'

	def format(self, data):
		return json.dumps(data)

class HDF5Storage(StorageFormatter):

	def __init__(self, *args, **kwargs):
		super(HDF5Storage, self).__init__(*args, **kwargs)

		self.foldername = 'hdf5'

	def format(self, data):
		pass

class StorageFormatterFactory(object):
	
	@staticmethod	
	def getInstance(class_name, *args, **kwargs):
		try:
			instance = getattr(sys.modules[__name__], class_name)
			obj = instance(*args, **kwargs)
			return obj
		except:
			raise Exception("Could not instantiate class {0}".format(class_name))