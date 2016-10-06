# -*- coding: u8 -*-
import numpy as np
import struct
import socket
import time
import sys

from libsoundannotator.streamboard               import processor
from libsoundannotator.streamboard.continuity    import Continuity

class streamInput(processor.InputProcessor):

    """ Reads samples from an AF_INET stream, using the SensorCity protocol:
    
                The protocol for audiodata uses a standard internet socket (AF_INET) on port 3000, 
                the Sensor City Foundation maintains a list of IP addresses for the Sensor City Sound VLAN.
                
                The incoming stream packets are formatted as follows (in order of appearance):
                    32 bits: "magic byte" providing a check on packet 
                    64 bits: "double" seconds unix/posix time, marks the time at the start of the packet
                    16 bits: "int" v
                    number of audio samples times 32 bits: "float" audio sample

                At present node ID can be extracted from the third block of the node IP address and 
                the microphone ID from the fourth block (xxx.xxx.NodeID.MicrophoneID).
                
                The samplerate is 96000 Hz.

        Parameters:
        DeviceIndex: set to the OS sound device index you want to use
                     for input
        SampleRate: in Hz
        ChunkSize: the number of samples you want to read and return
                   per  chunk
    """
    
    def __init__(self, *args, **kwargs):
        super(streamInput, self).__init__(*args, **kwargs)
        self.requiredParameters('SampleRate', 'ChunkSize', 'HOST','PORT')
        self.requiredParametersWithDefault( magicByte=0x2442, fs=96000, packaging_type='float32',reconnecttimeout=0.05)
        self.framesPerChunk=self.config['ChunkSize']
        self.nodeAddress=(self.config['HOST'],self.config['PORT'])
        self.magicByte=self.config['magicByte']
        self.fs=self.config['fs']
        self.reconnecttimeout=self.config['reconnecttimeout']
        
        if self.config['packaging_type']=='float32':
            self.output_dtype=np.float32
            self.packaging_bytes=4
        elif self.config['packaging_type']=='int16':
            self.output_dtype=np.int16
            self.packaging_bytes=2
            
        self.continuity=Continuity.discontinuous
        self.soundstring=''
        
    def prerun(self):
        '''
            Create socket
        '''
        self.addlogger()
        self.connect()
        self.resetBuffer()
        
        
    def resetBuffer(self):
        '''
            Buffer variables
        '''
        self.nframes=0
        self.soundstring=''
        
    def connect(self):
        '''
            (Re)Create socket and connect to it.
        '''
        self.socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        #self.logger.info('connect to nodeAddress: {0}'.format(self.nodeAddress))
        
        try:
            self.socket.connect(self.nodeAddress)
            self.logger.info('Now connected to nodeAddress: {0}'.format(self.nodeAddress))
            self.connected=True
        except:
            e = sys.exc_info()[0]
            self.logger.warning('Connecting to node {0} failed with exception: {1}'.format(self.nodeAddress,e))
            self.connected=False
        
    def reconnect(self):
        self.logger.warning('Reconnect needed for node: {0}'.format(self.nodeAddress))
        
        if self.connected==True:
            self.socket.close()
            
        time.sleep(self.reconnecttimeout)
        self.connect()
        self.resetBuffer()
        
    def streamAvailable(self):
        magicByteString=''
        streamAvailable=False
        
        if self.connected==True:
            try:
                magicByteString=self.socket.recv(4)
            except socket.error as e:
                self.logger.warning('Socket Error: {0}'.format(e)) 
        
            if len(magicByteString)==4:
                magicByte=struct.unpack('i',magicByteString)[0]
                streamAvailable=(magicByte==self.magicByte)
            
            if not streamAvailable:
                self.logger.error('Incorrect or absent MagicByteString: {0}'.format(magicByteString)) 
            
        return streamAvailable
        

        
        
    def generateData(self):
        dataout=dict()
        
        interruptedConnection=False
        
        
        while self.nframes < self.framesPerChunk:  # If we still have a large number of frames or we just gathered enough go on and publish
            if self.streamAvailable():
                self.currentTimeStamp=struct.unpack('d',self.socket.recv(8))[0]
                newframes=struct.unpack('h',self.socket.recv(2))[0]
                self.nframes+=newframes
                n=newframes*self.packaging_bytes
                
                received=0
                while received < n:
                    data = self.socket.recv(n-received) #Non blocking if connection established and node can be reached, blocks when you unplug ethernet cable.
                    received    +=len(data)
                    self.soundstring+=data
            else: #
                self.reconnect()
                interruptedConnection=True
        '''
            unpack string
        '''
        sound = np.frombuffer(self.soundstring[:self.framesPerChunk*self.packaging_bytes],self.output_dtype)
        self.soundstring=self.soundstring[self.framesPerChunk*self.packaging_bytes:]
        self.nframes-=self.framesPerChunk
        
        dataout['sound'] = sound
        dataout['HOST']  = self.config['HOST']
        dataout['PORT']  = self.config['PORT']
        
        if interruptedConnection: # Mark this chunk as discontinuous with previous
            self.continuity=Continuity.discontinuous
        else:                   # This restores continuity parameter, when previous chunk was discarded as invalid
            self.continuity=Continuity.withprevious
        
        return dataout
    
    def finalize(self):
        self.socket.close()
   
