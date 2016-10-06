import json
import os
import numpy as np

#import background model
from bgmodel import BGModel
from bgmodelmanager import BGModelManager

#streamboard classes
import libsoundannotator.streamboard as streamboard

from streamboard.processor  import Processor
from streamboard.continuity import Continuity


class ConfigLoader(object):
    def __init__(self, filename, **kwargs):
        self.directory = kwargs.get('directory', os.path.dirname(os.path.realpath(__file__)) + '/')
        self.filename = filename

    def exists(self):
        try:
            with open(self.directory + self.filename) as jsonfile: 
                return True
        except IOError:
            return False

    def get(self):
        if not hasattr(self, 'config'):
            self.load()
        return self.config

    def load(self):
        with open(self.directory + self.filename) as json_file:
            self.config = json.load(json_file)

        json_file.close()

    def save(self, models):
        try:
            with open(self.directory + self.filename, 'wb') as json_file:
                json.dump(models, json_file)
                print "Config file written."
        except IOError, e:
            print "Oops, something went wrong with writing config: {0}. Try again".format(e)


class BackgroundModelProcessor(Processor):

    requiredKeys = ['EdB']

    def __init__(self, *args, **kwargs):
        super(BackgroundModelProcessor, self).__init__(*args, **kwargs)
        self.requiredParameters('ModelsFile','SampleRate')

        loader = ConfigLoader(self.config['ModelsFile'])
        self.modelconfig = loader.get()

    def prerun(self):
        super(BackgroundModelProcessor,self).prerun()
        #initialize the different background models specified in the config
        self.models = dict()

        #create manager 
        self.manager = BGModelManager(self.modelconfig)

    def processData(self, injection):
        chunk = injection.received['EdB']
        self.logger.info("Processing chunk")
        #skip first and last chunk (ask Tjeerd for good solution?)
        if chunk.number == 1 or chunk.continuity == Continuity.last:
            return None

        #for each BG model, inject the EdB into the model and retrieve the results.
        return {'features': self.manager.calculateChunk(chunk)}
