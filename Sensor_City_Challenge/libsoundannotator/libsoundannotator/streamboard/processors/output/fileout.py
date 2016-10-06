from libsoundannotator.streamboard               import processor
from libsoundannotator.streamboard.continuity    import Continuity
from libsoundannotator.io.storage                import StorageFormatterFactory

from libsoundannotator.io.API import BadRequestException, BadFormatException
from requests.exceptions import ConnectionError
import os, time, glob, sys, datetime
import numpy as np
import h5py

class ServalOutputProcessor(processor.OutputProcessor):
    def __init__(self, *args, **kwargs):
        super(ServalOutputProcessor, self).__init__(*args, **kwargs)
        self.requiredParameters('outdir', 'maxFileSize','nodeName')
        self.requiredParametersWithDefault(
            #insert credentials here
            sensorId = kwargs.get('sensorId', None),
            moduleId = kwargs.get('moduleId', None),
            resourceId = kwargs.get('resourceId', None),
            endpoint = kwargs.get('endpoint', None),
            classType = "ServalStorage",
            requiredKeys=kwargs.get('requiredKeys',self.requiredKeys)
        )
        self.requiredKeys=self.config['requiredKeys']
        self.previousStartTime = None

    def prerun(self):
        super(ServalOutputProcessor, self).prerun()
        self.storageformatter = StorageFormatterFactory.getInstance(self.config["classType"],
            sensorId = self.config['sensorId'],
            moduleId = self.config['moduleId'],
            resourceId=self.config['resourceId'],
            endpoint=self.config['endpoint'],
            logger=self.logger
        )

    def processData(self, smartChunk):
        indicators = smartChunk.received['indicators']
        try:
            self.storageformatter.store(indicators, smartChunk.startTime, metadata)
        except ConnectionError as e:
            self.logger.error('Unable to connect to API: {0}'.format(e.message))
        except BadFormatException as e:
            self.logger.warning(e)
        except BadRequestException as e:
            self.logger.warning('Could not POST chunk to API: {0}'.format(e))
        except ValueError as e:
            self.logger.error('Value Error with storage response: {0}'.format(e))
        except Exception as e:
            raise e
        finally:
            self.continuity = Continuity.discontinuous


class APIOutputProcessor(processor.OutputProcessor):
    def __init__(self, *args, **kwargs):
        super(APIOutputProcessor, self).__init__(*args, **kwargs)
        self.requiredParameters('outdir', 'maxFileSize','nodeName')
        self.requiredParametersWithDefault(
            #insert credentials here
            key = kwargs.get('APIKEY', None),
            secret = kwargs.get('APISECRET', None),
            uid = kwargs.get('API_UID', None),
            api = kwargs.get('API', None),
            classType = "APIStorage",
            requiredKeys=kwargs.get('requiredKeys',self.requiredKeys),
            timeTolerance = kwargs.get('timeTolerance', 60) #seconds
        )
        self.requiredKeys=self.config['requiredKeys']
        self.previousStartTime = None

    def prerun(self):
        super(APIOutputProcessor, self).prerun()
        self.storageformatter = StorageFormatterFactory.getInstance(self.config["classType"],
            APIKEY = self.config['key'],
            APISECRET = self.config['secret'],
            API_UID=self.config['uid'],
            API=self.config['api'],
            nodeName=self.config['nodeName'],
            logger=self.logger
        )

    def processData(self, smartChunk):
        metadata = smartChunk.chunkMetaData
        metadata['continuity'] = smartChunk.continuity
        self.logger.info("Received smart chunk with metadata: {0}".format(metadata))

        #if time diverges too much from previous time, create a new point as well
        if self.previousStartTime != None and abs(self.previousStartTime - smartChunk.startTime) > self.config['timeTolerance']:
            self.logger.warning("Chunk times diverge too much (threshold is {0} seconds). Forcing new data point in API".format(self.config['timeTolerance']))
            self.storageformatter.rollover()

        #if discontinuous, force new file
        if smartChunk.continuity == Continuity.discontinuous or smartChunk.continuity == Continuity.newfile or smartChunk.continuity == Continuity.invalid:
            self.logger.info("Encountered discontinuity. Flushing and setting new file")
            #force increment in new file
            self.storageformatter.rollover(metadata)

        if not smartChunk.continuity == Continuity.last:
            for key in smartChunk.received.keys():
                representation=self.config['representations'].get(key, None)
                self.logger.info("Store chunk with key {0}, POST key {1}".format(key, representation))
                chunk = smartChunk.received[key]

                if chunk.data.size == 0:
                    continue

                self.logger.info(chunk.data)
                try:
                    if chunk.data.dtype != self.config['datatype']:
                        #convert to config data type if possible
                        chunk.data = chunk.data.astype(self.config['datatype'])
                    self.storageformatter.store(key, smartChunk.startTime, chunk, metadata,
                        representation=representation
                    )
                except ConnectionError as e:
                    self.logger.error('Unable to connect to API: {0}'.format(e.message))
                except BadFormatException as e:
                    self.logger.warning(e)
                except BadRequestException as e:
                    self.logger.warning('Could not POST chunk to API. Marking as discontinuous: {0}'.format(e))
                    self.storageformatter.rollover()
                except ValueError as e:
                    self.logger.error('Value Error with storage response: {0}'.format(e))
                except Exception as e:
                    raise e
                finally:
                    self.continuity = Continuity.discontinuous

            self.previousStartTime = smartChunk.startTime


"""
    ATTENTION: THIS OUTPUT PROCESSOR STILL HAS ISSUES, IT DOESN'T WORK CORRECTLY. USE WITH CAUTION
"""
class FileOutputProcessor(processor.OutputProcessor):
    requiredKeys = ["data"]

    def __init__(self, *args, **kwargs):
        super(FileOutputProcessor, self).__init__(*args, **kwargs)
        self.requiredParameters('outdir', 'classType', 'maxFileSize')
        self.requiredParametersWithDefault(
            outdir = os.path.join(os.path.expanduser("~"), "data", "libsoundannotator"),
            classType = "HDF5Storage",
            maxFileSize = 104857600, #100M in bytes
            datatype = 'int16'
        )

        self.fileExt = 'hdf5'
        self.startNum = 1

    def prerun(self):
        super(FileOutputProcessor, self).prerun()
        self.storageformatter = StorageFormatterFactory.getInstance(self.config["classType"],
            outdir=self.config['outdir'],
            logger=self.logger,
            dtype=self.config['datatype']
        )

    def processData(self, smartChunk):
        metadata = smartChunk.chunkMetaData
        self.logger.info("Received smart chunk with metadata: {0}".format(metadata))

        #if discontinuous, force new file
        if smartChunk.continuity == Continuity.discontinuous:
            self.logger.warning("Encountered discontinuity. Flushing and setting new file")
            #force increment in new file
            self.storageformatter.rollover(metadata)

        for key in smartChunk.received:
            chunk = smartChunk.received[key]
            self.storageformatter.store(key, smartChunk.startTime, chunk, metadata)
