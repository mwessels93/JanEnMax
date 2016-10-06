import numpy as np

from libsoundannotator.streamboard import processor

class AudioRelayProcessor(processor.Processor):
    '''
        Processor for relaying audio to the network
    '''
    requiredKeys = ['sound']

    def __init__(self, boardConn, name, *args, **kwargs):
        super(AudioRelayProcessor, self).__init__(boardConn, name, *args, **kwargs)
        self.requiredParameters('SampleRate')

    def processData(self, compositeChunk):
        chunk = compositeChunk.received['sound']

        return {
        	'sound': chunk.data
        }