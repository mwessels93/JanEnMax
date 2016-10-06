# -*- coding: u8 -*-
import multiprocessing, logging, time, sys, inspect, os, glob
import numpy as np
import signal


# Streamboard architecture
from libsoundannotator.streamboard.board              import Board
from libsoundannotator.streamboard.continuity         import Continuity
from libsoundannotator.streamboard.subscription       import SubscriptionOrder, NetworkSubscriptionOrder

# Streamboard processors
from libsoundannotator.streamboard.processors.input   import noise, sine, mic, wav, sensorcity, text
from libsoundannotator.cpsp                           import oafilterbank
from libsoundannotator.cpsp                           import tfprocessor                 # import GCFBProcessor
from libsoundannotator.cpsp                           import structureProcessor          # import structureProcessor, structureProcessorCalibrator
from libsoundannotator.cpsp                           import patchProcessor              # import patchProcessor, FloorQuantizer, textureQuantizer
from libsoundannotator.cpsp                           import structuredEnergyProcessor   # import structuredEnergyProcessor
from libsoundannotator.cpsp                           import PTN_Processor               # import PTN_Processor


from libsoundannotator.cpsp import LeakyIntProcessor

from libsoundannotator.streamboard.processors.output.oldfileout  import FileOutputProcessor
from libsoundannotator.streamboard.processors.output.image       import HDF5ImageProcessor
from libsoundannotator.streamboard.processors.output             import util as oututil
from libsoundannotator.streamboard.processors._processor.sourceindicator import SourceIndicatorProcessor


# Version info generated for this build
from  soundannotatordemo.config import runtimeMetaData

# Auxilary software for argument parsing
import soundannotatordemo.config.argparser as argparser

# File information management
from libsoundannotator.io.annotations                 import FileAnnotation

from libsoundannotator.streamboard               import processor

def run():
    # Main should initialize logging for multiprocessing package
    logger = multiprocessing.log_to_stderr()
    logger.setLevel(args.loglevel)
    b = Board(loglevel=args.loglevel, logdir=args.logdir, logfile='inputtohdf') # Setting loglevel is needed under windows
    if args.calibrate or args.whitenoise:
        if args.calibrate:
            ChunkSize=11*args.inputrate
            calibration=True
        else:
            ChunkSize=args.ChunkSize
            calibration=False
        b.startProcessor('SoundInput',noise.NoiseChunkGenerator,
            SampleRate=args.inputrate,
            ChunkSize=ChunkSize,
            metadata=args.metadata,
            noofchunks=100,
            calibration=calibration
        )
    elif args.soundfiles != None:
        with open(args.soundfiles) as fileListGenerator:
            code = compile(fileListGenerator.read(), args.soundfiles, 'exec')
            exec code
        b.startProcessor('SoundInput', wav.WavProcessor,
            ChunkSize=args.ChunkSize,
            SoundFiles=soundfiles,
            timestep=0.0,
            AddWhiteNoise=10e-10,
            metadata=args.metadata
        )
    elif args.wav != None:
        if os.path.isdir(args.wav):
            logger.info("WAV argument points to wav folder {0}".format(args.wav))
            wavfiles = glob.glob("{0}/*.wav".format(args.wav))
            if len(wavfiles) == 0:
                raise Exception("Found no wav files in indicated folder")
            logger.info("Found {0} wav files in folder".format(len(wavfiles)))
        elif os.path.isfile(args.wav):
            logger.info("WAV argument points to single wav file")
            wavfiles = [args.wav]
        else:
            logger.error('Invalid specification of wav-file location')
            exit()
        soundfiles = []
        for wavfile in wavfiles:
            soundfiles.append( FileAnnotation(wavfile, wavfile) )
        args.soundfiles=True
        b.startProcessor('SoundInput', wav.WavProcessor,
            ChunkSize=args.ChunkSize,
            SoundFiles=soundfiles,
            timestep=0.0,
            metadata=args.metadata,
            startLatency=3.0,
            AddWhiteNoise=2**2-1,
            #newFileContinuity=Continuity.discontinuous
        )
    elif args.sinewave:
        b.startProcessor('SoundInput', sine.SineWaveGenerator,
            SampleRate=args.inputrate,
            ChunkSize=args.ChunkSize,
            metadata=args.metadata
        )
    elif args.batch:
        b.startProcessor('SoundInput', text.TextBatchInputProcessor,
            SampleRate=args.inputrate,
            ChunkSize=args.ChunkSize,
            timestep=0.0,
            startLatency=3.0,
            batchfile=args.batch,
            metadata=args.metadata
        )
    else:
        b.startProcessor('SoundInput', mic.MicInputProcessor,
            SampleRate=args.inputrate,
            ChunkSize=args.ChunkSize,
            nChannels = 1,
            Frequency=args.frequency,
            metadata=args.metadata
        )
    if args.decimation > 1:
        b.startProcessor('Resampler', oafilterbank.Resampler, SubscriptionOrder('SoundInput','Resampler','sound','timeseries'),
            SampleRate=args.inputrate,
            FilterLength=1000,
            DecimateFactor = args.decimation,
            dTypeIn=np.complex64,
            dTypeOut=np.complex64
        )
        myTFProcessorSubscriptionOrder=SubscriptionOrder('Resampler','TFProcessor','timeseries','timeseries')
    else:
        myTFProcessorSubscriptionOrder=SubscriptionOrder('SoundInput','TFProcessor', 'sound','timeseries')

    samplesPerFrame=args.samplesperframe
    InternalRate=args.inputrate/args.decimation
    InternalRate2=InternalRate/samplesPerFrame

    b.startProcessor('TFProcessor', tfprocessor.GCFBProcessor, myTFProcessorSubscriptionOrder,
        SampleRate=InternalRate,
        fmin=40,
        fmax=InternalRate/2,
        nseg=args.noofscales,
        samplesPerFrame=samplesPerFrame,
        scale='ERBScale',
        baseOutputDir=args.outdir,
        globalOutputPathModifier=runtimeMetaData.outputPathModifier,
        dTypeIn=np.complex64,
        dTypeOut=np.complex64,
        metadata=args.metadata,
    )


    # Streamboard machine learning


    cachename='StructureExtractorCache'
    if args.calibrate:
        b.startProcessor('StructureExtractor',
                          structureProcessor.structureProcessorCalibrator,
                          SubscriptionOrder('TFProcessor','StructureExtractor','EdB','TSRep'),
                          noofscales=args.noofscales,
                          cachename=cachename,
                          SampleRate=InternalRate2)
    else:
        b.startProcessor('StructureExtractor_F',
                          structureProcessor.structureProcessor,
                          SubscriptionOrder('TFProcessor','StructureExtractor_F','EdB','TSRep'),
                          noofscales=args.noofscales,
                          cachename=cachename,
                          textureTypes=['f'],
                          SampleRate=InternalRate2)
        b.startProcessor('StructureExtractor_S',
                          structureProcessor.structureProcessor,
                          SubscriptionOrder('TFProcessor','StructureExtractor_S','EdB','TSRep'),
                          noofscales=args.noofscales,
                          cachename=cachename,
                          textureTypes=['s'],
                          SampleRate=InternalRate2)

        b.startProcessor('PTNE',PTN_Processor.MaxTract_Processor,
                SubscriptionOrder('TFProcessor','PTNE','E','E'),
                SubscriptionOrder('StructureExtractor_F','PTNE','f_tract','f_tract'),
                SubscriptionOrder('StructureExtractor_S','PTNE','s_tract','s_tract'),
                featurenames=['pulse','tone','noise','energy','tsmax','tfmax','tsmin','tfmin'],
                noofscales=args.noofscales,
                split=eval(args.ptnsplit),
                SampleRate=InternalRate2,
                blockwidth=args.ptnblockwidth,
                ptnreferencevalue = args.ptnreferencevalue,
            )

        b.startProcessor('SourceIndicator', SourceIndicatorProcessor,
            SubscriptionOrder('PTNE','SourceIndicator','energy','energy'),
            SubscriptionOrder('PTNE','SourceIndicator','pulse','pulse'),
            SubscriptionOrder('PTNE','SourceIndicator','noise','noise'),
            SubscriptionOrder('PTNE','SourceIndicator','tone','tone'),
            prototypeDir=os.path.join(os.path.expanduser('~'), '.sa', 'prototypes')
        )
        b.startProcessor("FileWriter-PTNE", FileOutputProcessor,
                SubscriptionOrder('PTNE','FileWriter-PTNE','energy','energy'),
                SubscriptionOrder('PTNE','FileWriter-PTNE','pulse','pulse'),
                SubscriptionOrder('PTNE','FileWriter-PTNE','noise','noise'),
                SubscriptionOrder('PTNE','FileWriter-PTNE','tone','tone'),
                SubscriptionOrder('PTNE','FileWriter-PTNE','tsmax','tsmax'),
                SubscriptionOrder('PTNE','FileWriter-PTNE','tfmax','tfmax'),
                SubscriptionOrder('PTNE','FileWriter-PTNE','tsmin','tsmin'),
                SubscriptionOrder('PTNE','FileWriter-PTNE','tfmin','tfmin'),
                outdir=os.path.join(args.outdir, 'ptne'),
                maxFileSize=args.maxFileSize,
                datatype = 'float32',
                requiredKeys=['pulse','tone','noise','energy','tsmax','tfmax','tsmin','tfmin'],
                usewavname=True,
                metadata=args.metadata,
            )
        b.startProcessor("ImageGenerator", HDF5ImageProcessor,
            SubscriptionOrder('PTNE', 'ImagerGenerator', 'energy', 'energy'),
            basedir=os.path.join(args.outdir, 'ptne', 'hdf5'),
            usewavname=True,
            metadata=args.metadata
        )

    # GUI Elements
    if args.guimode == 'timescale_logE':
        print('=============== Start timescale viewer on log(E) ====================')
        from libsoundannotator.cpsp import tf_plotter
        toMyTFProcessor=b.getConnectionToProcessor(SubscriptionOrder('TFProcessor','toTFProcessor','EdB','EdB'))
        tfv=tf_plotter.tf_viewer(args.ChunkSize/2, args.noofscales, toMyTFProcessor,logger, lowValue=0 , highValue=240, datakey='EdB')
        tfv.run()

    if args.guimode == 'timescale_patch':
        b.startProcessor('PatchExtractor_F',
                            patchProcessor.patchProcessor,
                            SubscriptionOrder('StructureExtractor_F','PatchExtractor_F','f_tract','TSRep'),
                            quantizer=patchProcessor.textureQuantizer(),
                            noofscales=args.noofscales,
                            SampleRate=InternalRate2)
        #b.startProcessor('PatchExtractor_S', patchProcessor, SubscriptionOrder('StructureExtractor_S','PatchExtractor_S','s_tract','TSRep'), quantizer=textureQuantizer(),noofscales=noofscales,SampleRate=InternalRate2)
        print('=============== Start timescale viewer on patches====================')
        from libsoundannotator.cpsp import tf_plotter
        toMyPatchExtractor=b.getConnectionToProcessor(SubscriptionOrder('PatchExtractor_F','toPatchExtractor','levels','P'))
        tfv=tf_plotter.tf_viewer(args.ChunkSize, args.noofscales, toMyPatchExtractor,logger, lowValue=-1 , highValue=2, datakey='P')
        tfv.run()

    if args.guimode == 'timescale_struct':
        print('=============== Start timescale viewer on structure ====================')
        from libsoundannotator.cpsp import tf_plotter
        toMyStructureExtractor=b.getConnectionToProcessor(SubscriptionOrder('StructureExtractor_F','toStructureExtractor','f_tract','T'))
        tfv=tf_plotter.tf_viewer(args.ChunkSize, args.noofscales, toMyStructureExtractor, logger, lowValue=0 , highValue=100, datakey='T')
        tfv.run()

    if args.guimode == 'timescale_pattern':
        print('=============== Start timescale viewer on structure ====================')
        from libsoundannotator.cpsp import tf_plotter
        toMyStructureExtractor=b.getConnectionToProcessor(SubscriptionOrder('StructureExtractor_S','toStructureExtractor','s_pattern','T'))
        tfv=tf_plotter.tf_viewer(args.ChunkSize, args.noofscales, toMyStructureExtractor, logger, lowValue=0 , highValue=100, datakey='T')
        tfv.run()

    if args.guimode == 'li_trace':
        print('====================Start sound_viewer====================')
        from libsoundannotator.cpsp import tf_plotter
        toLIStream  = b.getConnectionToProcessor(SubscriptionOrder('LeakyIntProcessor_PTNE','toLIStream','pulse','channel1' ))
        toLIStream2  = b.getConnectionToProcessor(SubscriptionOrder('LeakyIntProcessor_PTNE','toLIStream','pulse_average','channel1' ))
        sv=tf_plotter.sound_viewer(toLIStream,toLIStream2,logger,30, 1, 10, -10,150)
        sv.run()

    if args.guimode == 'soundtrace':
        print('====================Start sound_viewer====================')
        from libsoundannotator.cpsp import tf_plotter
        toSoundStream  = b.getConnectionToProcessor(SubscriptionOrder('SoundInput','toSoundStream','sound','channel1' ))
        toSampleStream = b.getConnectionToProcessor(SubscriptionOrder('Resampler','toSampleStream','timeseries','channel2'))
        sv=tf_plotter.sound_viewer(toSoundStream,toSampleStream,logger,
            3, args.decimation, args.inputrate)
        sv.run()

    sleeptime=1
    continuity=Continuity.withprevious
    if not args.guimode =='nogui':
        pass
    else:
        if args.calibrate:
            toProbeProcessor=b.getConnectionToProcessor(SubscriptionOrder('StructureExtractor','toProbeProcessor','cacheCreated','cacheCreated'))
            terminationValueContinuity=Continuity.calibrationChunk
        else:
            toProbeProcessor=b.getConnectionToProcessor(SubscriptionOrder('TFProcessor','toProbeProcessor','technicalkey','technicalkey'))
            terminationValueContinuity=Continuity.last
            sleeptime+=10

        toProbeProcessor.riseConnection(logger)
        toProbeProcessor=toProbeProcessor.connection
        while continuity!=terminationValueContinuity:
            new = toProbeProcessor.poll(0.25)
            if new:
                chunk= toProbeProcessor.recv()
                continuity=chunk.continuity

    signal.signal(signal.SIGINT,b.stop)
    if args.calibrate:
        time.sleep(10)
        b.stopallprocessors()
    else:
        while b.isHealthy():
            time.sleep(2)
        time.sleep(5)
        b.stopallprocessors()


commandlinestring=' '.join(sys.argv)
args = argparser.getArguments(commandlinestring,
                               pypath=argparser.abspathFromMethod(run)
                            )

if __name__ == '__main__':
    run()
