from libsoundannotator.cpsp.bgmodel import bgmodel
from libsoundannotator.cpsp.buffer import WindowedChunkBuffer2D
import os, numpy as np, logging, random

class SourceIndicator(object):

    def __init__(self, model, *args, **kwargs):
        if 'logger' in kwargs:
            self.logger = kwargs.get('logger')
        else:
            self.logger = logging.getLogger('SourceIndicator')
        self.model = model
        self.name = model['name']
        self.bgmodelresponses = dict((k, None) for k in self.model['requiredKeys'])
        #load the prototype that belongs to this
        d = kwargs.get('prototypeDir', None)
        if not d:
            raise Exception('No directory given to load prototypes from ("prototypeDir kwarg")')

        filepath = os.path.join(d, '{}.npy'.format(self.model['name']))
        if not os.path.isfile(filepath):
            raise Exception('Unable to find file "{}.npy" in prototype dir "{}"'.format(self.model['name'], d))

        self.prototype = np.load(filepath)
        #check shape of prototype against model band distributions

        #initialize the buffer based on the prototype length
        self.buffer = WindowedChunkBuffer2D(self.prototype.shape, **kwargs)

    def wants(self):
        return self.model['requiredKeys']

    def calculate(self):
        startband = 0
        signal = None
        for idx, key in enumerate(self.model['requiredKeys']):
            if self.bgmodelresponses[key] is None:
                raise Exception("Model {} needs key {}, but key is not present in calculated responses".format(self.name, key))

            # create an array of windowed signals
            inputsignal = self.bgmodelresponses[key]
            if signal is None:
                signal = np.zeros((self.prototype.shape[0], inputsignal.shape[1]))
                self.logger.debug("Signal shape: {}".format(signal.shape))

            # bands information
            bands = self.model['bands'][idx]
            # first tuple entry is band key, make sure it's correct
            if bands[0] != key:
                raise Exception('Model bands order incorrect. Expected key {}, got {}'.format(key, self.model['bands'][idx][0]))

            # low idx, high idx from response signal
            (low, high) = (bands[1], bands[2])
            self.logger.debug('from {} to {} for key {}'.format(low, high, key))
            self.logger.debug('place bands {} - {} in {} - {}'.format(low, high, startband, startband + (high-low)))
            signal[startband:startband+(high-low),:] = inputsignal[low:high,:]
            startband = high-low

        n = self.buffer.add(signal)
        if n > 0:
            windows = [w for w in self.buffer.getBuffers()]
            for idx, w in enumerate(windows):
                windows[idx] = np.sum(w * self.prototype) / w.size
            #compare with prototype
            self.logger.info('Got {} windows with shape {}'.format(len(windows), windows[0].shape))
            return windows

        self.bgmodelresponses = dict((k, None) for k in self.model['requiredKeys'])
        return None

    def compare(self, window):
        return scipy.signal.correlate2d(window, self.prototype)

    def setBGModel(self, key, response):
        if not key in self.bgmodelresponses:
            raise Exception("Key {} is not known in model required keys. Cannot store BG response".format(key))
        self.bgmodelresponses[key] = response

    def emptyBuffer(self):
        self.buffer.empty()
