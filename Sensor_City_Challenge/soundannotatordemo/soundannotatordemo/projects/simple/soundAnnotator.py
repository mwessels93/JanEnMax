# -*- coding: u8 -*-
import multiprocessing, logging, time, sys, inspect, os, glob
import numpy as np
import signal

import matplotlib
matplotlib.use('WXAgg')
'''
tested working backends: GTKAgg, TkAgg, WXAgg 
tested failing backends: Agg, Cairo, qt4agg, GTK3Agg, gtk3cairo,gtk
'''


# Streamboard architecture

from libsoundannotator.streamboard.board              import Board
#from libsoundannotator.tests.streamboard_test.streamboard_testing_tools import TestBoard as Board

from libsoundannotator.streamboard.continuity         import Continuity
from libsoundannotator.streamboard.subscription       import SubscriptionOrder, NetworkSubscriptionOrder

# Streamboard processors
from libsoundannotator.streamboard.processors.input   import noise, sine, mic, wav, sensorcity
from libsoundannotator.cpsp                           import oafilterbank
from libsoundannotator.cpsp                           import tfprocessor                 # import GCFBProcessor
from libsoundannotator.cpsp                           import structureProcessor          # import structureProcessor, structureProcessorCalibrator
from libsoundannotator.cpsp                           import patchProcessor              # import patchProcessor, FloorQuantizer, textureQuantizer
from libsoundannotator.cpsp                           import structuredEnergyProcessor   # import structuredEnergyProcessor
from libsoundannotator.cpsp                           import PTN_Processor               # import PTN_Processor


from libsoundannotator.cpsp import LeakyIntProcessor

from libsoundannotator.streamboard.processors.output.oldfileout  import FileOutputProcessor
from libsoundannotator.streamboard.processors.output.fileout     import APIOutputProcessor


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
    
    
    b = Board(loglevel=args.loglevel, logdir=args.logdir, logfile='soundAnnotator') # Setting loglevel is needed under windows

    def stopallboards(dummy1='1',dummy2='2'):
        b.stopallprocessors()
        time.sleep(1)
        sys.exit('')

    signal.signal(signal.SIGINT, stopallboards)

    if args.calibrate or args.whitenoise:
        if args.calibrate:
            ChunkSize=11*args.inputrate
            calibration=True
        else:
            ChunkSize=args.ChunkSize
            calibration=False
        #logger.setLevel(logging.DEBUG)
        b.startProcessor('S2S_SoundInput',noise.NoiseChunkGenerator,
            SampleRate=args.inputrate,
            ChunkSize=ChunkSize,
            metadata=args.metadata,
            noofchunks=100,
            calibration=calibration
        )
    elif args.soundfiles != None:
        fileListGeneratorSandbox=dict()
        with open(args.soundfiles) as fileListGenerator:
            code = compile(fileListGenerator.read(), args.soundfiles, 'exec')
            exec code in fileListGeneratorSandbox
        b.startProcessor('S2S_SoundInput', wav.WavProcessor,
            ChunkSize=args.ChunkSize,
            SoundFiles=fileListGeneratorSandbox['soundfiles'],
            timestep=0.5,
            AddWhiteNoise=args.whiten,
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

        b.startProcessor('S2S_SoundInput', wav.WavProcessor,
            ChunkSize=args.ChunkSize,
            SoundFiles=soundfiles,
            timestep=0.08,
            metadata=args.metadata,
            #newFileContinuity=Continuity.discontinuous
        )
    elif args.sinewave:
        b.startProcessor('S2S_SoundInput', sine.SineWaveGenerator,
            SampleRate=args.inputrate,
            ChunkSize=args.ChunkSize,
            metadata=args.metadata
        )
    elif args.node !=None:
        node=dict()
        node['id']=args.node[0]
        node['host']=args.node[1]
        node['port']=int(args.node[2])

        print('{0},{1},{2}'.format(node['id'],node['host'],node['port']))
        b.startProcessor('S2S_SoundInput',sensorcity.streamInput,
            SampleRate=args.inputrate,
            ChunkSize=args.ChunkSize,
            nodeID=node['id'],
            HOST=node['host'],
            PORT=node['port'],
            packaging_type='float32',
            metadata=args.metadata
        )
    else:
        b.startProcessor('S2S_SoundInput', mic.MicInputProcessor,
            SampleRate=args.inputrate,
            ChunkSize=args.ChunkSize,
            nChannels = 1,
            Frequency=args.frequency,
            metadata=args.metadata,
        )


    if args.decimation > 1:
        b.startProcessor('S2S_Resampler', oafilterbank.Resampler, SubscriptionOrder('S2S_SoundInput','S2S_Resampler','sound','timeseries'),
            SampleRate=args.inputrate,
            FilterLength=1000,
            DecimateFactor = args.decimation,
            dTypeIn=np.complex64,
            dTypeOut=np.complex64
        )
        myTFProcessorSubscriptionOrder=SubscriptionOrder('S2S_Resampler','S2S_TFProcessor','timeseries','timeseries')
    else:
        myTFProcessorSubscriptionOrder=SubscriptionOrder('S2S_SoundInput','S2S_TFProcessor', 'sound','timeseries')

    samplesPerFrame=args.samplesperframe
    InternalRate=args.inputrate/args.decimation
    InternalRate2=InternalRate/samplesPerFrame

    b.startProcessor('S2S_TFProcessor', tfprocessor.GCFBProcessor, myTFProcessorSubscriptionOrder,
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


    cachename='S2S_StructureExtractorCache'
    if args.calibrate:
        b.startProcessor('S2S_StructureExtractor',
                          structureProcessor.structureProcessorCalibrator,
                          SubscriptionOrder('S2S_TFProcessor','S2S_StructureExtractor','EdB','TSRep'),
                          noofscales=args.noofscales,
                          cachename=cachename,
                          SampleRate=InternalRate2)
    else:
        b.startProcessor('S2S_StructureExtractor_F',
                          structureProcessor.structureProcessor,
                          SubscriptionOrder('S2S_TFProcessor','S2S_StructureExtractor_F','EdB','TSRep'),
                          noofscales=args.noofscales,
                          cachename=cachename,
                          textureTypes=['f'],
                          SampleRate=InternalRate2)
        b.startProcessor('S2S_StructureExtractor_S',
                          structureProcessor.structureProcessor,
                          SubscriptionOrder('S2S_TFProcessor','S2S_StructureExtractor_S','EdB','TSRep'),
                          noofscales=args.noofscales,
                          cachename=cachename,
                          textureTypes=['s'],
                          SampleRate=InternalRate2)

        if args.vEA:
            b.startProcessor('vEA',structuredEnergyProcessor.structuredEnergyProcessor,
                    SubscriptionOrder('S2S_TFProcessor','vEA','E','E'),
                    SubscriptionOrder('S2S_StructureExtractor_F','vEA','f_tract','f_tract'),
                    SubscriptionOrder('S2S_StructureExtractor_S','vEA','s_tract','s_tract'),
                    SubscriptionOrder('S2S_StructureExtractor_F','vEA','f_pattern','f_pattern'),
                    SubscriptionOrder('S2S_StructureExtractor_S','vEA','s_pattern','s_pattern'),
                    noofscales=args.noofscales,
                    split=eval(args.ptnsplit),
                    SampleRate=InternalRate2,
                    baseOutputDir=args.outdir,
                    globalOutputPathModifier=runtimeMetaData.outputPathModifier,
                    NumpyOut=True,MatlabOut=False,MatricesOut=True,
                    cli=commandlinestring, svnBranch=runtimeMetaData.branch,
                    svnversion=runtimeMetaData.version,
                    blockwidth=args.ptnblockwidth,
                    )


        if args.PTNE:

            b.startProcessor('S2S_PTNE',PTN_Processor.PartialPTN_Processor,
                    SubscriptionOrder('S2S_TFProcessor','S2S_PTNE','E','E'),
                    SubscriptionOrder('S2S_StructureExtractor_F','S2S_PTNE','f_tract','f_tract'),
                    SubscriptionOrder('S2S_StructureExtractor_S','S2S_PTNE','s_tract','s_tract'),
                    featurenames=['pulse','tone','noise','energy'],
                    noofscales=args.noofscales,
                    split=eval(args.ptnsplit),
                    SampleRate=InternalRate2,
                    blockwidth=args.ptnblockwidth,
                    ptnreferencevalue = args.ptnreferencevalue,
                )
            '''    '''


            # dump data to file
            #'''
            b.startProcessor("S2S_FileWriter-PTNE", FileOutputProcessor,
                    #SubscriptionOrder('S2S_TFProcessor','S2S_FileWriter-PTNE','E','E'),
                    #SubscriptionOrder('S2S_StructureExtractor_F','S2S_FileWriter-PTNE','f_tract','f_tract'),
                    #SubscriptionOrder('S2S_StructureExtractor_S','S2S_FileWriter-PTNE','s_tract','s_tract'),
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','energy','energy'),
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','pulse','pulse'),
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','noise','noise'),
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','tone','tone'),
                    outdir=os.path.join(args.outdir,runtimeMetaData.outputPathModifier+'-'+args.metadata['script_started'],'ptne'),
                    maxFileSize=args.maxFileSize,
                    datatype = 'float32',
                    requiredKeys=['pulse','tone','noise','energy'],
                    #requiredKeys=['pulse','tone','noise','energy','E','f_tract','s_tract'],
                    usewavname=True,
                    metadata=args.metadata,
                )


            b.startProcessor("S2S_FileWriter-Tracts", FileOutputProcessor,
                    SubscriptionOrder('S2S_TFProcessor','S2S_FileWriter-PTNE','E','E'),
                    SubscriptionOrder('S2S_StructureExtractor_F','S2S_FileWriter-PTNE','f_tract','f_tract'),
                    SubscriptionOrder('S2S_StructureExtractor_S','S2S_FileWriter-PTNE','s_tract','s_tract'),
                    outdir=os.path.join(args.outdir,runtimeMetaData.outputPathModifier+'-'+args.metadata['script_started'],'tracts'),
                    maxFileSize=args.maxFileSize,
                    datatype = 'float32',
                    requiredKeys=['E','f_tract','s_tract'],
                    usewavname=True,
                    metadata=args.metadata,
                )
            
            cachedir=os.path.join(os.path.expanduser('~'),'data','libsoundannotator')
            """b.startProcessor("S2S_LeakyIntProcessor_PTNE", LeakyIntProcessor.LeakyIntProcessor,
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','energy','energy'),
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','pulse','pulse'),
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','noise','noise'),
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','tone','tone'),
                    requiredKeys=['energy','pulse','noise','tone'],
                    cachedir=cachedir,
                    maxFileSize=np.power(2,24),
                    period='second',
                    blockwidth=args.ptnblockwidth,
                    )"""

            # dump data to file
            '''
            b.startProcessor("S2S_FileWriter-LI", FileOutputProcessor,
                    SubscriptionOrder('S2S_LeakyIntProcessor_PTNE','S2S_FileWriter-LI','energy','energy'),
                    SubscriptionOrder('S2S_LeakyIntProcessor_PTNE','S2S_FileWriter-LI','pulse','pulse'),
                    SubscriptionOrder('S2S_LeakyIntProcessor_PTNE','S2S_FileWriter-LI','noise','noise'),
                    SubscriptionOrder('S2S_LeakyIntProcessor_PTNE','S2S_FileWriter-LI','tone','tone'),
                    outdir=os.path.join(args.outdir,runtimeMetaData.outputPathModifier+'-'+args.metadata['script_started'],'ptne_li'),
                    maxFileSize=args.maxFileSize,
                    datatype = 'float32',
                    requiredKeys=['pulse','tone','noise','energy'],
                    metadata=args.metadata,
                )
            '''

            '''




            b.startProcessor('S2S_APIOutput-PTNE', APIOutputProcessor,
                    #SubscriptionOrder('S2S_TFProcessor','S2S_APIOutput-PTNE','E','E'),
                    #SubscriptionOrder('S2S_StructureExtractor_F','S2S_APIOutput-PTNE','f_tract','f_tract'),
                    #SubscriptionOrder('S2S_StructureExtractor_S','S2S_APIOutput-PTNE','s_tract','s_tract'),
                    SubscriptionOrder('S2S_PTNE','S2S_APIOutput-PTNE','energy','loudness'),
                    #SubscriptionOrder('S2S_PTNE','S2S_APIOutput-PTNE','pulse','pulse'),
                    #SubscriptionOrder('S2S_PTNE','S2S_APIOutput-PTNE','noise','noise'),
                    #SubscriptionOrder('S2S_PTNE','S2S_APIOutput-PTNE','tone','tone'),
                    outdir=args.outdir,
                    maxFileSize=args.maxFileSize,
                    datatype = 'float32',
                    #requiredKeys=['pulse','tone','noise','energy'],
                    representations={
                        'pulse': 'audio_pulse',
                        'noise': 'audio_noise',
                        'tone': 'audio_tone',
                        'loudness': 'audio_loudness'
                    },
                    # API base URL
                    API = 'http://test.sndrc.nl:1337',
                    # name of the desired Dataset: see http://test.sndrc.nl:1337/dataset for possible datasets
                    nodeName = 'Node1',
                    # the API public key of the consumer we want to use
                    key = "a12ead32-a4f3-4462-9188-e362e95c8748",
                    # The API secret key
                    secret= "80940fbc-1de5-4893-8440-4cb988ad7ebd",
                    # The UID of the 'system' user we use to POST data to the API
                    uid = "55e5d253e3cf102c250a4ff0"
                )
            '''


    # GUI Elements
    if args.guimode == 'timescale_logE':
        print('=============== Start timescale viewer on log(E) ====================')
        from libsoundannotator.cpsp import tf_plotter
        toMyTFProcessor=b.getConnectionToProcessor(SubscriptionOrder('S2S_TFProcessor','toS2S_TFProcessor','EdB','EdB'))
        tfv=tf_plotter.tf_viewer(args.ChunkSize/2, args.noofscales, toMyTFProcessor,logger, lowValue=0 , highValue=240, datakey='EdB')
        tfv.run()

    if args.guimode == 'timescale_patch':
        b.startProcessor('S2S_PatchExtractor_F',
                            patchProcessor.patchProcessor,
                            SubscriptionOrder('S2S_StructureExtractor_F','S2S_PatchExtractor_F','f_tract','TSRep'),
                            quantizer=patchProcessor.textureQuantizer(),
                            noofscales=args.noofscales,
                            SampleRate=InternalRate2)
        #b.startProcessor('S2S_PatchExtractor_S', patchProcessor, SubscriptionOrder('S2S_StructureExtractor_S','S2S_PatchExtractor_S','s_tract','TSRep'), quantizer=textureQuantizer(),noofscales=noofscales,SampleRate=InternalRate2)
        print('=============== Start timescale viewer on patches====================')
        from libsoundannotator.cpsp import tf_plotter
        toMyPatchExtractor=b.getConnectionToProcessor(SubscriptionOrder('S2S_PatchExtractor_F','toS2S_PatchExtractor','levels','P'))
        tfv=tf_plotter.tf_viewer(args.ChunkSize, args.noofscales, toMyPatchExtractor,logger, lowValue=-1 , highValue=2, datakey='P')
        tfv.run()

    if args.guimode == 'timescale_struct':
        print('=============== Start timescale viewer on structure ====================')
        from libsoundannotator.cpsp import tf_plotter
        toMyStructureExtractor=b.getConnectionToProcessor(SubscriptionOrder('S2S_StructureExtractor_F','toS2S_StructureExtractor','f_tract','T'))
        tfv=tf_plotter.tf_viewer(args.ChunkSize, args.noofscales, toMyStructureExtractor, logger, lowValue=0 , highValue=100, datakey='T')
        tfv.run()

    if args.guimode == 'timescale_pattern':
        print('=============== Start timescale viewer on structure ====================')
        from libsoundannotator.cpsp import tf_plotter
        toMyStructureExtractor=b.getConnectionToProcessor(SubscriptionOrder('S2S_StructureExtractor_S','toS2S_StructureExtractor','s_pattern','T'))
        tfv=tf_plotter.tf_viewer(args.ChunkSize, args.noofscales, toMyStructureExtractor, logger, lowValue=0 , highValue=100, datakey='T')
        tfv.run()

    if args.guimode == 'li_trace':
        print('====================Start sound_viewer====================')
        from libsoundannotator.cpsp import tf_plotter
        toLIStream  = b.getConnectionToProcessor(SubscriptionOrder('S2S_LeakyIntProcessor_PTNE','toLIStream','pulse','channel1' ))
        toLIStream2  = b.getConnectionToProcessor(SubscriptionOrder('S2S_LeakyIntProcessor_PTNE','toLIStream','pulse_average','channel1' ))
        sv=tf_plotter.sound_viewer(toLIStream,toLIStream2,logger,30, 1, 10, -10,150)
        sv.run()

    if args.guimode == 'soundtrace':
        print('====================Start sound_viewer====================')
        from libsoundannotator.cpsp import tf_plotter
        toSoundStream  = b.getConnectionToProcessor(SubscriptionOrder('S2S_SoundInput','toSoundStream','sound','channel1' ))
        toSampleStream = b.getConnectionToProcessor(SubscriptionOrder('S2S_Resampler','toSampleStream','timeseries','channel2'))
        sv=tf_plotter.sound_viewer(toSoundStream,toSampleStream,logger,
            3, args.decimation, args.inputrate,ymin=-10000,  ymax=10000)
        sv.run()

    print('====================Main sleeps 1 s====================')
    sleeptime=1
    print('====================Main awakens====================')
    continuity=Continuity.withprevious
    if not args.guimode =='nogui':
        pass
    else:
        if args.calibrate:
            toProbeProcessor=b.getConnectionToProcessor(SubscriptionOrder('S2S_StructureExtractor','toProbeProcessor','cacheCreated','cacheCreated'))
            terminationValueContinuity=Continuity.calibrationChunk
        else:
            toProbeProcessor=b.getConnectionToProcessor(SubscriptionOrder('S2S_TFProcessor','toProbeProcessor','technicalkey','technicalkey'))
            terminationValueContinuity=Continuity.last
            print('====================Main sleeps 10 s ====================')
            sleeptime+=10
            print('====================Main awakens====================')

        toProbeProcessor.riseConnection(logger)
        toProbeProcessor=toProbeProcessor.connection
        while continuity!=terminationValueContinuity:
            #b.recv_from_processor(0.05)
            new = toProbeProcessor.poll(0.25)
            if new:
                chunk= toProbeProcessor.recv()
                continuity=chunk.continuity


    print('====================Let processors finish unfinished business====================')
    time.sleep(sleeptime)
    print('====================Wake up and exit====================')
    b.stopallprocessors()


commandlinestring=' '.join(sys.argv)
args = argparser.getArguments(commandlinestring,
                               pypath=argparser.abspathFromMethod(run)
                            )

if __name__ == '__main__':
    run()
