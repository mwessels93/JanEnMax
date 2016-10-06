import json, os, sys, time, glob, h5py, datetime, numpy as np, pytz
from libsoundannotator.io.API import APIRequest, BadRequestException
from libsoundannotator.streamboard import logger
from libsoundannotator.streamboard.continuity import Continuity

class StorageFormatter(object):

    def __init__(self, *args, **kwargs):
        self.logger = kwargs.get('logger', None)

    def format(self, data):
        raise Exception("Implement this in subclass")

    def store(self, key, timestamp, data, metadata, **kwargs):
        raise Exception("Implement this in subclass")

    def rollover(self, metadata):
        raise Exception("Implement this in subclass")

class ServalStorage(StorageFormatter):
    def __init__(self, *args, **kwargs):
        super(ServalStorage, self).__init__(*args, **kwargs)
        self.makeNew = True
        self.sensorId = kwargs.get('sensorId')
        self.moduleId = kwargs.get('moduleId')
        self.resourceId = kwargs.get('resourceId')

    def store(self, indicators, timestamp, metadata, **kwargs):
        indicatorValue = chunk.data
        request = {
            "datetime": time.time(),
            "sensor": self.sensorId,
            "modules": [{
                "id": self.moduleId,
                "resources": [{
                    "id": self.resourceId,
                    "value": {
                        "indicators": indicators
                    }
                }]
            }]
        }
        self.logger.info(request)

class APIStorage(StorageFormatter):

    def __init__(self, *args, **kwargs):
        super(APIStorage, self).__init__(*args, **kwargs)
        self.request = APIRequest(
            key=kwargs.get('APIKEY'),
            secret=kwargs.get('APISECRET'),
            uid=kwargs.get('API_UID'),
            API=kwargs.get('API')
        )
        self.makeNew = True
        self.nodeName=kwargs.get('nodeName')
        #get dataset ID
        response = self.request.get('/dataset?name={0}'.format(self.nodeName))
        if response.status_code != 200:
            raise BadRequestException(response.text)
        resp_json = response.json()
        if len(resp_json) == 0:
            raise BadRequestException('Dataset {0} is not found in API'.format(self.nodeName))
        dataset = resp_json[0]
        self.datasetID = dataset['id']
        print "Dataset {0}".format(self.datasetID)

    def store(self, key, timestamp, chunk, metadata, **kwargs):
        #right now, we only accept 1 value per call

        #change internal frequency to that of the previously publishing processor (in this case PTNE)
        metadata['frequency'] = metadata['ptnblockwidth']
        if len(chunk.data.shape) > 1:
            raise BadRequestException('Data shape exceeds acceptable dimension (1): {0}'.format(chunk.data.shape))
        if chunk.data.size > 1:
            raise BadRequestException('More than one element in chunk data, unable to POST: {0} elements'.format(chunk.data.size))

        #convert chunk.data to singular value
        chunk.data = chunk.data[0]

        representation = kwargs.get('representation')
        if representation is None:
            if self.logger:
                self.logger.error('Cannot send to API with missing "representation field"')
            else:
                print '[ERROR] Cannot send to API with missing "representation field"'
            return

        #bit hacky way to adhere to the JS timestamp format for MongoDB
        created_at = datetime.datetime.utcfromtimestamp(timestamp).isoformat()[:-3]+'Z'
        if self.logger:
            self.logger.debug('Formatted datetime: {0}'.format(created_at))
        else:
            print 'Formatted datetime: {0}'.format(created_at)
        if self.makeNew:
            request_url = '/data/stream/{0}'.format(representation)
            POSTbody = {
                representation: chunk.data,
                "dataset": self.datasetID,
                "datetime": created_at,
                "info": json.dumps(metadata)
            }
            if self.logger:
                self.logger.info('new data point: {0}'.format(POSTbody))
            else:
                print 'new data point: {0}'.format(POSTbody)

        else:
            request_url = '/data/{0}/stream/{1}'.format(self.dataID, representation)
            POSTbody = {
                representation: chunk.data,
                "datetime": created_at
            }
        response = self.request.post(request_url, POSTbody)
        if response.status_code != 200:
            raise BadRequestException('HTTP Status {0}'.format(response.status_code))
        else:
            #store the returned data ID
            self.dataID = response.json()['data']['id']
            if self.makeNew:
                # set makeNew to false, since we've created this data point to be
                # used by all subsequent representations
                self.makeNew = False

    def rollover(self, metadata):
        self.makeNew = True

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
        self.fileExt = 'hdf5'
        self.startNum = 1 #initially, start at 1
        self.basedir = os.path.join(kwargs.get('outdir'), self.foldername)
        self.dtype = kwargs.get('dtype', None)
        self.maxFileSize = kwargs.get('maxFileSize', 104857600)

        #call to resolve directories. Bubbles an exception if some things are not right
        self.resolvedDir = self.resolveOutdir()

        #key cache
        self.cache = dict()
        self.maxCacheSize = kwargs.get('maxCacheSize', 10) #accepts kwarg, default is 10 chunks
        self.cachemeta = dict()

    def format(self, data):
        pass

    def store(self, key, timestamp, data, metadata, **kwargs):
        #convert the data to the specified data type if it is set
        if not self.dtype == None:
            data.data = data.data.astype(self.dtype)

        #resolve outdir at each call to store, to make sure nothing is missing to store data
        self.resolveOutdir()
        if not key in self.cache:
            self.cache[key] = []

        if len(self.cache[key]) >= self.maxCacheSize:
            #flush the key from cache. This stores all cached data chunks to file
            self.flush(key, metadata)
        else:
            #create new cache meta entry if empty
            if not key in self.cachemeta:
                self.cachemeta[key] = dict()
            #check the metadata against the reference value for this key.
            #if something differs, this means trouble. For security purposes, raise exception
            if not self.sameMetadata(self.cachemeta[key], metadata):
                raise Exception("New chunk's metadata differs from reference value")
            #cache the chunk
            self.putInCache(key, data)

    def putInCache(self, key, data):
        if not key in self.cache:
            self.cache[key] = []

        self.cache[key].append(data)

    def flush(self, key, metadata):
        self.logger.debug("Flushing '{0}' from cache".format(key))
        #recursive call to flush all cache keys in case of 'all' keyword
        if key == "all":
            for key in self.cache:
                self.flush(key, metadata)
        else:
            #resolve data file. This also makes sure that a valid file handle is being returned
            h5pyf = self.resolveDataFile(self.resolvedDir, metadata['location'].replace(' ', ''))
            for chunk in self.cache[key]:
                self.addChunkToDataset(h5pyf, key, chunk)
            h5pyf.close()
            self.cache[key] = []

    def rollover(self, metadata):
        self.logger.info("Preparing for file rollover")
        self.flush("all", metadata)
        #force file increment
        h5pyf = self.resolveDataFile(self.resolvedDir, metadata['location'].replace(' ', ''), True)
        h5pyf.close()

    def resolveOutdir(self):
        if not os.path.isdir(self.basedir):
            self.logger.info("Base outdir does not exist. Creating output directory: {0}".format(self.basedir))
            try:
                os.makedirs(self.basedir)
            except Exception as e:
                self.logger.error("Unable to create directories: {0}".format(e))
                return

        now = datetime.date.today()
        foldername = now.strftime('%Y-%m-%d')
        todaydir = os.path.join(self.basedir, foldername)
        if not os.path.isdir(todaydir):
            self.logger.info("Current-day folder does not exist. Creating output folder {0}".format(foldername))
            try:
                os.makedirs(todaydir)
                return todaydir
            except Exception as e:
                self.logger.error("Unable to create output folder: {0}".format(e))
                return
        else:
            self.logger.info("Storing to output directory {0}".format(todaydir))
            return todaydir


    def resolveDataFile(self, basedir, location, forceNewFile=False):
        # look if there are files with 'location' in their name in the basedir
        # following the convention <location>.*.<ext>
        self.logger.info(basedir)
        files = sorted(glob.glob(os.path.join(basedir, "{0}.*.{1}".format(location, self.fileExt))))
        if len(files) == 0:
            num = self.startNum
        else:
            # try to parse the number by removing the ext,
            # then splitting on the dot and casting the last entry to int
            num = int(files[-1][:-(len(self.fileExt) + 1)].split('.')[-1])

            #if forceNewFile, up the number by one
            if forceNewFile:
                num += 1
            #if filesize is too large, increment as well
            else:
                abspathToFile = os.path.join(basedir, "{0}.{1}.{2}".format(location, num, self.fileExt))
                size = os.stat(abspathToFile).st_size
                if size >= self.maxFileSize:
                    self.logger.info("Current file's size too large: {0} vs. max {1}"
                        .format(size, self.maxFileSize)
                    )
                    num += 1

        #file number resolved, setting it class-wide now
        self.startNum = num

        filename = "{0}.{1}.{2}".format(location, self.startNum, self.fileExt)
        self.logger.info("Resolved filename {0}".format(filename))
        #open or create
        h5pyf = h5py.File(os.path.join(basedir, filename))

        return h5pyf

    def addChunkToDataset(self, h5pyf, key, chunk):
        maxshape = (None,)
        shapeDim = 0

        if not key in h5pyf:
            #based on the dimensionality, define maxshape. if 1D, this dimension is resizable.
            # if 2D, columns are resizable
            if len(chunk.data.shape) == 2:
                maxshape = (chunk.data.shape[0], None)
                shapeDim = 1
            elif len(chunk.data.shape) > 2:
                self.logger.error("Unsupported nr. of dimensions to define maxshape: {0}".format(len(chunk.data.shape)))

            #create a new data set for this key, resizable in column direction
            dset = h5pyf.create_dataset(key,
                shape=chunk.data.shape,
                dtype=self.dtype,
                maxshape=maxshape,
                compression="gzip",
                compression_opts=9,
            )
        else:
            dset = h5pyf[key]

        # dset is available, call reshape using the current shape and the chunk's
        # column length
        dset.resize(dset.shape[shapeDim] + chunk.data.shape[shapeDim], shapeDim)
        # place the chunk's data at the end in its place
        if len(chunk.data.shape) == 1:
            dset[-chunk.data.shape[shapeDim]:] = chunk.data
        elif len(chunk.data.shape) == 2:
            dset[:, -chunk.data.shape[shapeDim]:] = chunk.data
        else:
            raise Exception("Cannot append {0}D data".format(len(chunk.data.shape)))

        if len(h5pyf.attrs) == 0:
            self.addClientMetadata(h5pyf, self.cachemeta[key])
        #call to embed the chunk's meta data into the data set
        self.addChunkMetadata(dset, chunk)

    def addClientMetadata(self, h5pyf, metadata):
        for key in metadata:
            h5pyf.attrs[key] = metadata[key]

    def sameMetadata(self, cachemeta, metadata):
        for key in metadata:
            #if meta is available in stored reference...
            if key in cachemeta:
                # ...but current value differs, print warning
                if str(cachemeta[key]) != str(metadata[key]):
                    self.logger.warning("New client meta data mismatch on key {0} :{1} vs. {2}"
                        .format(key, cachemeta[key], metadata[key])
                    )
                    return False
            else:
                self.logger.info("Setting {0} = {1} in cache meta".format(key, metadata[key]))
                val = metadata[key]
                #'escape' None or False to prevent crash later on when writing to hdf5 file
                if val == False or val == None:
                    val = str(val)
                #set the meta data
                cachemeta[key] = val

        return True

    def addChunkMetadata(self, dset, chunk):
        #check if 'starttime' attr is set, if not set it
        if not 'starttime' in dset.attrs:
            dset.attrs['starttime'] = chunk.dataGenerationTime
        #always update 'endtime' with chunk's current 'dataGenerationTime'
        dset.attrs['endtime'] = chunk.dataGenerationTime

class StorageFormatterFactory(object):

    @staticmethod
    def getInstance(class_name, *args, **kwargs):
        try:
            instance = getattr(sys.modules[__name__], class_name)
            obj = instance(*args, **kwargs)
            return obj
        except Exception as e:
            raise Exception("Could not instantiate class {0}: {1}".format(class_name, e))
