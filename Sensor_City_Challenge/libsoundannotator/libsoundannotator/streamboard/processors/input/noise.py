import numpy as np
import time

from libsoundannotator.streamboard               import processor
from libsoundannotator.streamboard.continuity    import Continuity

class NoiseChunkGenerator(processor.InputProcessor):

    """ NoiseChunkGenerator:
            Does what you expect from the name

        Parameters:
            SampleRate: in Hz
            ChunkSize: the number of samples you want to read and return
                       per block
    """

    def __init__(self, *args, **kwargs):
        super(NoiseChunkGenerator, self).__init__(*args, **kwargs)
        self.requiredParameters('SampleRate', 'ChunkSize')
        self.requiredParametersWithDefault(noofchunks=1, calibration=False)
        self.runno=0
        self.startframe=-self.config['ChunkSize'] 
        self.noofchunks=self.config['noofchunks']
        self.calibration=self.config['calibration']
        if(self.calibration and self.noofchunks >1):
            self.logmsg['info'].append('Calibration use a single chunk: Noofchunks reset to 1')
            self.noofchunks=1
            
    def prerun(self):
        super(NoiseChunkGenerator, self).prerun()
        subscription = False
        while not subscription:
            self.checkAndProcessBoardMessage()
            if(len(self.subscriptions) >0):
                subscription = True
        self.startframe=0

    def generateData(self):
        data=None
        dataout=None

        if(self.runno < self.noofchunks):
            self.runno+=1
            
            dataout=dict()
            time.sleep(self.config['ChunkSize']/self.config['SampleRate'])
            data=np.random.randn(self.config['ChunkSize'])
            
            self.continuity=Continuity.withprevious
            
            if(self.runno == self.noofchunks):
                if self.calibration:
                    self.continuity=Continuity.calibrationChunk
                else:
                    self.continuity=Continuity.last
            
            self.startframe+=self.config['ChunkSize']
                
                
            dataout['sound']=data
            

        time.sleep(0.05)
        return dataout
