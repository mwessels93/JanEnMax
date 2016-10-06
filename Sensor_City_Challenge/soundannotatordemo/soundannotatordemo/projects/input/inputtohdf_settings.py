import os, logging

settings = {
    'maxFileSize' : 1048576000, #HDF5 output max size, 1000MB in bytes
    'outdir' : os.path.join(os.path.expanduser('~'),'data'),
    'loglevel': logging.DEBUG,
    'logdir' : os.path.join(os.path.expanduser('~'),'.sa'),
    'inputrate': 44100, #for microphone only, WAV is auto recognized
    'ptnsplit': '['+','.join([str(i) for i in range(10,120)])+']', #frequency band splits, first 10 and last 10 are discarded
    'ptnblockwidth' : 0.005, #block width in seconds, determines outgoing sample rate
    'samplesperframe': 5,
    'noofscales': 133, #number of frequency bands in cochleogram
    'decimation': 2, #amount the inputrate is resampled. New Nyquist frequency becomes (inputrate / decimation)
    'frequency' : 5, #input publish frequency. Determines only how often data from the microphone is published
}
