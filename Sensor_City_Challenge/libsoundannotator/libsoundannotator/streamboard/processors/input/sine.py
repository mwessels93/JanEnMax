import numpy as np, time

from libsoundannotator.streamboard               import processor
from libsoundannotator.streamboard.continuity    import Continuity

class SineWaveGenerator(processor.InputProcessor):

    """ SineWaveGenerator:
            Does what you expect from the name

        Parameters:
            SampleRate: in Hz
            ChunkSize: the number of samples you want to read and return
                       per block
    """

    def __init__(self, *args, **kwargs):
        super(SineWaveGenerator, self).__init__(*args, **kwargs)
        self.requiredParameters('SampleRate', 'ChunkSize')
        self.requiredParametersWithDefault(Frequency=1000)

    def prerun(self):
        super(SineWaveGenerator, self).prerun()
        subscription = False
        while not subscription:
            self.checkAndProcessBoardMessage()
            if(len(self.subscriptions) >0):
                subscription = True
        self.startframe=0

    def generateData(self):
        dataout=dict()
        self.logger.debug('Processor generate data for startframe:{0}'.format(self.startframe))
        f=self.config['Frequency']
        w=2*np.pi*f/self.config['SampleRate']
        sampleIndices=np.arange(self.startframe,self.startframe+self.config['ChunkSize'])
        data = 2000*np.sin(w*sampleIndices)
        self.startframe+=self.config['ChunkSize']
        time.sleep(float(self.config['ChunkSize'])/float(self.config['SampleRate']))
        dataout['sound']=data
        return dataout
