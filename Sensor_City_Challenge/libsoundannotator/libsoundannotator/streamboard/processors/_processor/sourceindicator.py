import numpy as np

from libsoundannotator.streamboard import processor
from libsoundannotator.cpsp.sourceindicators import indicator, config, util

class SourceIndicatorProcessor(processor.Processor):
    '''
        Processor for relaying audio to the network
    '''
    requiredKeys = ['energy', 'pulse', 'tone', 'noise']

    def __init__(self, boardConn, name, *args, **kwargs):
        super(SourceIndicatorProcessor, self).__init__(boardConn, name, *args, **kwargs)

    def prerun(self):
        super(SourceIndicatorProcessor, self).prerun()
        self.config['logger'] = self.logger
        self.indicators, self.models, self.bgmodels = util.initFromConfig(config, **self.config)

    def processData(self, compositeChunk):
        inputs = {}
        for name in compositeChunk.received:
            inputs[name] = compositeChunk.received[name].data
        util.calculateBGModels(inputs, self.indicators, self.bgmodels, normalize=True)
        result = {}

        for i in self.indicators:
            resp = i.calculate()
            if resp is not None:
                self.logger.info("Detector {} got value {}".format(i.name, resp))
                result[i.name] = resp

        if any([res is not None for res in result.values()]):
            return result
        else:
            return None
