import numpy as np, collections, logging, math

class ChunkBuffer(object):
    def __init__(self, shape, **kwargs):
        if 'logger' in kwargs:
            self.logger = kwargs.get('logger')
        else:
            self.logger = logging.getLogger('ChunkBuffer')
        self.shape = shape
        self.chunk = np.zeros(self.shape)
        self.chunklength = self.shape[1]
        self.remainder = None
        self.pointer = 0
        self.buffer = collections.deque()

        self.logger = kwargs.get('logger', logging.getLogger('ChunkBuffer'))

    def empty(self):
        self.chunk = np.zeros(self.shape)
        self.remainder = None
        self.pointer = 0

    def getBuffers(self):
        while len(self.buffer) is not 0:
            yield self.buffer.pop()

    def add(self):
        raise NotImplementedError

class ChunkBuffer1D(ChunkBuffer):
    def __init__(self, length, **kwargs):
        shape = (1, length)
        super(ChunkBuffer1D, self).__init__(shape, **kwargs)

    def add(self, signal):
        raise NotImplementedError


class ChunkBuffer2D(ChunkBuffer):
    def __init__(self, shape, **kwargs):
        super(ChunkBuffer2D, self).__init__(shape, **kwargs)

    def add(self, signal):
        signallength = signal.shape[1]
        signalpointer = 0
        available = self.chunklength - self.pointer
        self.logger.debug("Signal length {}, available {}".format(signallength, available))
        # is the input signal greater than the available chunk?
        if self.pointer + signallength > available:
            # do we have something in the chunk already?
            if available < self.chunklength:
                self.logger.debug("Copy remainder of length {} from chunk".format(available))
                #fill up the chunk, add it to the buffer, then handle the rest
                self.chunk[:, self.pointer:] = signal[:,:available]
                self.buffer.appendleft(np.copy(self.chunk))
                self.pointer = 0
                # shift the signal pointer to after the part we just assigned
                signalpointer = available
                available = self.chunklength

            # calculate how many times the signal fits in the chunk completely
            n = math.floor((signallength - signalpointer) / self.chunklength)
            self.logger.debug("Signal fits {} times in chunk".format(n))
            for i in range(n):
                # append directly to buffer
                newchunk = np.copy(signal[:,signalpointer:signalpointer+self.chunklength])
                self.logger.debug('New chunk of shape {} directly into buffer'.format(newchunk.shape))
                self.buffer.appendleft(newchunk)
                signalpointer += self.chunklength
                self.logger.debug('signalpointer is now {}'.format(signalpointer))

        self.logger.debug("Copy remaining {} frames from signal into chunk".format(signallength - signalpointer))
        # copy the remainder of the signal to the chunk, and remember the chunk pointer
        self.chunk = signal[:,signalpointer:]
        self.pointer = signallength - signalpointer

        self.logger.debug("Buffer size is now {}, chunk size is {}".format(len(self.buffer), self.pointer))
        return len(self.buffer)

class WindowedChunkBuffer2D(ChunkBuffer2D):

    def __init__(self, shape, **kwargs):
        super(WindowedChunkBuffer2D, self).__init__(shape, **kwargs)
        # window shift default is equal to buffer length (no overlap)
        self.shift = kwargs.get('windowShift', self.shape[1])
        self.logger.debug("set shift to {}".format(self.shift))

    def add(self, signal):
        signallength = signal.shape[1]
        signalpointer = 0
        available = self.chunklength - self.pointer
        self.logger.debug("Signal length {}, pointer {}, available {}".format(signallength, self.pointer, available))
        # if the signal doesn't fit in the buffer
        if signallength > available:
            #calculate how many shifts we can perform across the new signal
            overflow = signallength - available
            self.logger.debug("Overflow length {}".format(overflow))
            n, signalpointer = (int(math.floor(overflow / self.shift)), available)
            self.logger.debug("{} shifts, signalpointer starts at {}".format(n, signalpointer))
            #first add a new chunk to buffer
            self.chunk[:,self.pointer:] = signal[:,:signalpointer]
            self.buffer.appendleft(np.copy(self.chunk))
            for i in range(n):
                self.logger.debug("Shift {}".format(i))
                #roll chunk to left by shift amount
                self.chunk = np.roll(self.chunk, -self.shift, axis=1)
                self.logger.debug("Copy signal parts {}:{}".format(signalpointer,signalpointer+self.shift))
                # copy shift amount from signal
                self.chunk[:,-self.shift:] = signal[:,signalpointer:signalpointer+self.shift]
                self.buffer.appendleft(np.copy(self.chunk))
                signalpointer += self.shift
                self.logger.debug("Signalpointer is now {}".format(signalpointer))

            #shift the remainder
            remainder = signallength - signalpointer
            self.chunk = np.roll(self.chunk, -self.shift, axis=1)
            self.logger.debug("remainder is {}".format(remainder))
            self.chunk[:,self.chunklength-self.shift:self.chunklength-self.shift+remainder] = signal[:,signalpointer:]
            self.pointer = self.chunklength - self.shift + remainder
            self.logger.debug("chunk pointer is now at {}".format(self.pointer))

        else:
            self.chunk[:,self.pointer:self.pointer+signallength] = signal
            self.pointer += signallength
            self.logger.debug('chunk pointer is now {}'.format(self.pointer))

        return len(self.buffer)
