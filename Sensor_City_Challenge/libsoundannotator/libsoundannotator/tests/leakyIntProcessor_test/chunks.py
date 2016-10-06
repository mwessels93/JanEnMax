import numpy as np
import time


import libsoundannotator.streamboard.logger
from libsoundannotator.streamboard.continuity import Continuity, chunkAlignment

class DataChunk(object):
    """ A chunk of data, starting at a specific time and at a specific
        framerate
    """

    def __init__(self, data, startTime, fs, processorName, sources, continuity=Continuity.withprevious, number=0, alignment=chunkAlignment(), dataGenerationTime=False, identifier=None,metadata = None):
        self.processor = processorName

        assert(type(sources) is set)
        self.sources = sources

        self.data = data
        self.startTime = startTime
        self.fs = fs
        self.continuity=continuity
        self.number=number
        self.alignment=alignment
        self.dataGenerationTime = dataGenerationTime
        self.identifier = identifier
        self.metadata = metadata

    def getLength(self):
        return np.shape(self.data)[0]

    def setMetaData(self, metadata):
        self.metadata = metadata

    def getMetaData(self):
        return self.metadata


class smartCompositeChunk(object):
    """ A composite of chunk of data, deriving from the same preceding source chunk.
    """

    def __init__(self, requiredKeys, number, processor, continuity=Continuity.withprevious, predecessor=None):
        self.continuity=Continuity.withprevious
        self.sources=set()
        self.requiredKeys=frozenset(requiredKeys)
        self.openKeys=set(requiredKeys)
        self.received=dict()
        self.number=number
        self.predecessor=predecessor
        self.processor=processor
        self.successor=None
        self.startTime='Initial'
        self.chunkbuffer=dict(zip(requiredKeys,[None]*len(requiredKeys)))
        if predecessor==None:
            processor.logger.info('Created smartCompositeChunk chain for processor: {0} with requiredKeys: {1}'.format(processor,requiredKeys))


    def inject(self, receiverKey, chunk):
        #set identifier of current chunk
        self.identifier = chunk.identifier


        if self.predecessor==None:
            self.processor.logger.info('Chunk injection for processor: {0} with receiverKey: {1} , chunk continuity: {2}, chunk number: {3}'.format(self.processor,receiverKey,chunk.continuity,chunk.number))


        # If this chunk completes the composite we need to be sure there is a successor to claim future input
        if self.successor == None:
            self.successor= smartCompositeChunk(self.requiredKeys, self.number+1,
            self.processor, predecessor=self)

        if self.number == chunk.number:
            self.process(receiverKey, chunk)
        elif self.number > chunk.number:
                self.processor.logger.info('Drop preceding chunks, smart number {0}, chunk number {1}'.format(self.number,chunk.number))
                self.claimProcessor(self)
        elif self.number < chunk.number:
            self.successor.inject(receiverKey, chunk)

    def claimProcessor(self,callingchunk):
        self.processor.claim(self,callingchunk)
        if not self.predecessor == None:
            self.predecessor.dropreferences()
            self.predecessor=None

    def process(self, receiverKey, chunk):
        if receiverKey in self.openKeys:
                self.received[receiverKey]=chunk
                self.openKeys.remove(receiverKey)
                self.processor.logger.info('smartCompositeChunk received {0} chunk for processor {1}'.format(receiverKey,self.processor.name))
                self.processor.logger.debug('{0}: processor {1} received chunk {2}'.format(time.time(), self.processor.name, chunk.number))

        if len(self.openKeys)==0:
            self.preprocessChunks()
            self.chunkMetaData = chunk.getMetaData()
            data=self.processor.processData(self)   # This is where the processor is called to do the real work.
            self.processor.logger.debug("Got data in smartCompositeChunk")
            self.processor.publish(
                data, 
                chunk.dataGenerationTime, 
                metadata=self.chunkMetaData,
                identifier=chunk.identifier,
                alignment=self.alignment,
            )
            self.processor.logger.debug("Called publish on processor")
            self.successor.claimProcessor(self)

    def dropreferences(self):
        if self.predecessor == None:
                    pass
        else:
            self.predecessor.dropreferences()
            self.predecessor=None

        self.requiredKeys=None
        self.openKeys   =None
        self.successor  =None
        self.processor  =None
        self.received   =None

    def preprocessChunks(self):
        # Calculate continuity and sources from received chunks
        self.continuity=Continuity.withprevious
        self.chunkcontinuity=Continuity.withprevious
        self.sources=set([self.processor.name,])
        self.alignment=chunkAlignment()

        self.startTime='Initial'
        for key in self.received:
            chunk=self.received[key]
            self.sources=self.sources.union(chunk.sources)
            self.alignment=self.alignment.merge(chunk.alignment)
            if chunk.continuity != Continuity.withprevious:
                    self.continuity=chunk.continuity
                    self.chunkcontinuity=chunk.continuity

            if self.startTime != chunk.startTime and self.startTime =='Initial':
                self.startTime = chunk.startTime
            elif self.startTime != chunk.startTime:
                self.processor.logger.error('Inconsistent start time on incoming chunks')

            if self.startTime =='Initial':
                self.startTime=np.array([-1])

            self.processor.logger.info('Processor {0} received chunk no: {1} original time {2}'.format(self.processor.name,self.number,chunk.startTime))

        if self.continuity >= Continuity.withprevious and self.number != self.processor.previousClaimNumber+1:
            self.continuity=Continuity.discontinuous

        #Perform data over alignable chunks
        for key in self.received:
            chunk=self.received[key]
            buffered=self.chunkbuffer[key]
            self.chunkbuffer[key]=None

            if chunk.alignment.isAlignable():
                received=chunk.data
                dimension=len(np.shape(received))
                
                if buffered is None:
                    shape=np.zeros((dimension),dtype=np.int)
                    buffered=np.zeros(shape)
                
                self.processor.logger.info('smartCompositeChunk buffer shape: {0} received shape: {1} smart past {2},  chunk past: {3} key: {4} continuity:{5} chunkcontinuity: {6}'.format(
                    np.shape(buffered),np.shape(received),
                    self.alignment.includedPast,chunk.alignment.includedPast,
                    key,self.continuity,self.chunkcontinuity))
                self.processor.logger.debug('smartCompositeChunk align dimension: {0} self past: {1} chunk past: {2}'.format(
                    dimension,self.alignment.includedPast,
                    chunk.alignment.includedPast))

                if dimension == 1:
                    datalen=np.shape(received)[0]
                    bufferframes=datalen-(self.alignment.includedPast-chunk.alignment.includedPast)
                    if self.continuity >= Continuity.withprevious:
                        if np.size(buffered,axis=0) is not 0:
                            self.received[key].data=np.concatenate((buffered,received[:bufferframes]), axis=1)
                        else:
                            self.received[key].data=received[:bufferframes]
                    elif self.chunkcontinuity >= Continuity.withprevious:
                        self.received[key].data=received[chunk.alignment.includedPast:bufferframes]
                    else:
                        self.received[key].data=received[self.alignment.droppedAfterDiscontinuity-chunk.alignment.droppedAfterDiscontinuity:bufferframes]

                    self.successor.chunkbuffer[key]=received[bufferframes:]

                elif dimension == 2:
                    datalen=np.shape(received)[1]
                    bufferframes=datalen-(self.alignment.includedPast-chunk.alignment.includedPast)
                    if self.continuity >= Continuity.withprevious:
                        if  np.size(buffered,axis=1) is not 0:
                            self.received[key].data=np.concatenate((buffered,received[:,:bufferframes]), axis=1)
                        else:
                            self.received[key].data=received[:,:bufferframes]
                    elif self.chunkcontinuity >=  Continuity.withprevious:
                        self.received[key].data=received[:,chunk.alignment.includedPast:bufferframes]
                    else:
                        self.received[key].data=received[:,self.alignment.droppedAfterDiscontinuity-chunk.alignment.droppedAfterDiscontinuity:bufferframes]

                    self.successor.chunkbuffer[key]=received[:,bufferframes:]
                else:
                    self.processor.logger.error('smartCompositeChunk does not support numpy arrays of dimensions higher than 2')

            # Set continuity for all incoming chunks
            if chunk.continuity >= Continuity.withprevious:
                chunk.continuity=self.continuity

    def getcontinuity(self):
        return self.continuity



class initialSmartCompositeChunk(smartCompositeChunk):

    def inject(self, receiverKey, chunk):
        successor = smartCompositeChunk(
            self.requiredKeys, 
            chunk.number,
            self.processor, 
            predecessor=self
        )
        
        '''
          initialSmartCompositeChunk.number is initialized at -2 to make sure the first chunk will be discontinuos.
          This is done in the processor where in the __init__ a first DataChunk is defined with number = 0.
          
          preprocessChunks will spot the "dropped" chunk and flag the first smartChunk as discontinuos 
        '''
        self.number=successor.number-2   
        successor.claimProcessor(self)
        successor.inject(receiverKey, chunk)
