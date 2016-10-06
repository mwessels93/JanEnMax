import numpy as np

from libsoundannotator.streamboard import processor

class BeagleDataHandler(processor.Processor):
    '''
        Processor for receiving pickled data.
    '''
    requiredKeys = ['beagleData']

    def __init__(self, boardConn, name, *args, **kwargs):
        super(BeagleDataHandler, self).__init__(boardConn, name, *args, **kwargs)
        self.requiredParameters('outdir, output, SampleRate')
        self.logger.info("BeagleDataHandler initialization")

    def processData(self, compositeChunk):
        chunk = compositeChunk.received['beagleData']

        received = chunk.data

        result = dict()
        result['data'] = received
        self.logger.debug("BeagleDataHandler processed data: {0}".format(chunk.dataGenerationTime))
        if self.config['output']:
            import os
            import time
            import datetime

            date = datetime.datetime.fromtimestamp(time.time())
            outputfolder = self.config['outdir'] + "/{0}/{1}/{2}".format(date.year,date.month,date.day)
            #store the data in binary format in specific timestamp folders
            if not os.path.isdir(outputfolder):
                os.makedirs(outputfolder)

            try:
                np.save(outputfolder + "/{0}.npy".format(chunk.dataGenerationTime), received)
            except:
                self.logger.error("NPY file could not be saved")
                raise

        else:
            self.logger.info("No output specified")

        return result