import os, time, numpy as np

from libsoundannotator.streamboard                import processor
from libsoundannotator.streamboard.continuity     import Continuity

from libsoundannotator.io.annotations             import FileAnnotation
from libsoundannotator.io.csvinput                import CSVInputReader
from libsoundannotator.io.wavinput                import WavChunkReader
from libsoundannotator.io.hdfinput                import HdfChunkReader

class TextBatchInputProcessor(processor.InputProcessor):
    def __init__(self, conn, name, *args, **kwargs):
        super(TextBatchInputProcessor, self).__init__(conn, name, *args, **kwargs)

        self.requiredParameters('ChunkSize', 'SoundFiles', 'timestep', 'batchfile')
        self.requiredParametersWithDefault(AddWhiteNoise=None, newFileContinuity=Continuity.newfile, startLatency=3.0)
        
        self.chunksize = self.config['ChunkSize']
        self.timestep = self.config['timestep']
        self.AddWhiteNoise = self.config['AddWhiteNoise']
        self.newFileContinuity=self.config['newFileContinuity']
        self.startLatency = self.config['startLatency']
        
        self.batchfile = self.config['batchfile']
    
        if not os.path.isfile(self.batchfile):
            raise Exception("Batchfile is not an existing file: {}".format(self.batchfile))
        
        self.dirname = os.path.dirname(self.batchfile)
        if not os.path.isdir(self.dirname):
            raise Exception("Directory from batchfile doesn't exist: {}".format(self.dirname))
            
        #determine extension
        if self.batchfile.endswith('.csv'):
            self.soundfiles = []
            self.headers, rows = CSVInputReader(self.batchfile).read()
            for row in rows:
                audiofile = row['audiofile']
                del row['audiofile']
                del row['datetime']
                del row['createdAt']
                del row['updatedAt']
                if audiofile.endswith('.wav'):
                    storagetype = 'wav'
                elif audiofile.endswitth('.hdf5'):
                    storagetype = 'hdf'
                else:
                    raise Exception('Unable to process audiofile with this extension: {}'.format(audiofile))
                soundfile = FileAnnotation(audiofile, audiofile, storagetype)
                soundfile.setExtraArgs(row.keys(), row)
                self.soundfiles.append(soundfile)
                
    
    def run(self):
        self.prerun()
        self.logger.info("Processor {0} started".format(self.name))
        self.stayAlive = True
        self.checkAndProcessBoardMessage()
        self.logger.info("Sleeping for {} seconds".format(self.startLatency))
        time.sleep(self.startLatency)
        self.logger.info('got {} soundfiles'.format(len(self.soundfiles)))
        for idx,soundfile in enumerate(self.soundfiles):
            print "{}/{} input files".format(idx+1, len(self.soundfiles))
            self.processSoundfile(soundfile)

        self.publishlastchunk()
    
    def processSoundfile(self, soundfile):
        self.continuity = self.newFileContinuity

        self.sources = set([soundfile.uid])

        if soundfile.storagetype == 'wav':
            self.reader = WavChunkReader(os.path.join(self.dirname, soundfile.filename))
            #set extra metadata keys
            self.logger.info(soundfile.extra_args)
            for key in soundfile.extra_args.keys():
                self.oldchunk.metadata[key] = soundfile.extra_args[key]
            
            self.oldchunk.metadata['wav']=soundfile.filename
            self.oldchunk.metadata['duration']=self.reader.getDuration()
        elif soundfile.storagetype == 'hdf':
            self.reader = HdfChunkReader(soundfile.filename)
        else:
            raise Exception("Unknown storage type for soundfile: {0}".format(soundfile.storagetype))

        while (self.reader.hasFrames() and self.stayAlive):
            '''
                we call 'process', because this calls generateData with a chunk timestamp already.
                It also lets us intercept board messages
            '''

            self.process()
            self.checkAndProcessBoardMessage()
            '''
                Sleep is an artificial means of lowering the system load. Here it is done to allow
                chunks to propagate along other modules
            '''
            time.sleep(self.timestep)
            #set continuity
            self.continuity = Continuity.withprevious
    
    def generateData(self):
        frames = self.reader.readFrames(self.chunksize)

        # If specified, add some noise to prevent NaN from occuring due to log(E)
        if self.AddWhiteNoise:
            frames += self.generateWhitenoise(frames)

        data = {
            'sound' : frames
        }
        return data
            
    def generateWhitenoise(self,frames,addWhiteNoise=None):
        
        if addWhiteNoise is None:
            addWhiteNoise=self.AddWhiteNoise
        
        if addWhiteNoise is None:
            self.logger.error("generateWhitenoise called without valid value")
            raise TypeError("generateWhitenoise expects that a value is set for addWhiteNoise, received None")
            
        return ( addWhiteNoise * (np.random.rand(*np.shape(frames))-0.5)).astype(frames.dtype)
        
    def publishlastchunk(self):
        self.logger.debug("Publish last chunk")
        data=dict()
        
        frames = self.reader.getNullChunk(self.chunksize)
        if self.AddWhiteNoise:
            frames += self.generateWhitenoise(frames)
        elif issubclass(frames.dtype.type, np.integer):
            frames += self.generateWhitenoise(frames, addWhiteNoise=3)
        else:
            frames += self.generateWhitenoise(frames, addWhiteNoise=2**-100)
            
        data['sound'] =frames
        
        self.continuity=Continuity.last
        self.publish(data,self.continuity, self.getTimeStamp(None), self.getchunknumber(), time.time(), metadata=self.oldchunk.getMetaData())
        
        
