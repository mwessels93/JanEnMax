# Plotting 
import matplotlib
import matplotlib.pyplot as plt
'''
tested working backends: GTKAgg, TkAgg, WXAgg 
tested failing backends: Agg, Cairo, qt4agg, GTK3Agg, gtk3cairo,gtk
'''


# streamboard
from libsoundannotator.streamboard.processor  import Processor, Continuity
from libsoundannotator.streamboard.continuity import Continuity
from libsoundannotator.streamboard.subscription import Subscription

import numpy as np

import ctypes
import time
import sys

        
class  tf_viewer(object):
    def __init__(self, width, height, toTFRep, logger, datakey=None, lowValue=0, highValue=60, continuousBlockspacer=10,
        discontinuousBlockspacer=100,*args, **kwargs):
        
        super(tf_viewer, self).__init__(*args, **kwargs)
        self.continuousBlockspacer=continuousBlockspacer
        self.discontinuousBlockspacer=discontinuousBlockspacer
        self.logger=logger
        self.datakey=datakey 
        self.width=width
        self.height=height
        toTFRep.riseConnection(self.logger)
        self.toTFRep=toTFRep.connection
        self.matrix= np.random.randn(self.height, self.width)
        self.lowValue=lowValue
        self.highValue=highValue

    def run(self):
        self.prerun()
        self.stayAlive = True
        cnt=0
        while self.stayAlive:
            hasNew = self.toTFRep.poll(20)
            if hasNew:
                chunk = self.toTFRep.recv()
                self.update(chunk)
                self.draw() 
                if(sys.platform=='win32'):
                    cnt=cnt+1
                
                if cnt==20:
                    cnt=0
                    plt.close('all')                
                    time.sleep(0.001)
                    plt.ion()
                    self.prerun()
                    
                if(chunk.continuity==Continuity.last):
                        #plt.close(self.fig)
                        self.stayAlive=False
                        plt.ioff()
                        plt.close(self.fig)
        
        
    def setupimage(self):
        plt.ioff()
        self.fig = plt.figure(figsize=(20,6))
        self.ax = self.fig.add_subplot(111)
        self.canvas = self.ax.figure.canvas
        self.im=plt.imshow(self.matrix,axes=self.ax, interpolation='nearest', aspect='auto')#animated=True,
        self.im.set_clim(self.lowValue, self.highValue)
       

        #self.im = NonUniformImage(self.ax, interpolation='nearest',
        #    extent=(0,self.width,1,self.height), animated=True)

        self.ax.set_ylim(0,self.height)
        self.ax.set_xlim(0,self.width)
        self.x = np.linspace(0,self.width,self.width)
        self.y = np.linspace(0,self.height,self.height)
        self.background = self.canvas.copy_from_bbox(self.ax.get_figure().bbox)
        plt.show(block=False)
        self.canvas.draw()
        
    def prerun(self):        
        self.setupimage()
        
    
    def update(self,chunk):
        data=chunk.data
            
        continuity=chunk.continuity
        
        nSamples = np.shape(data)[1]
        
        if continuity>=Continuity.withprevious:
            blockSpacer=self.continuousBlockspacer
        else:
            blockSpacer=self.discontinuousBlockspacer
            
        if nSamples>0 :
            self.matrix[:, :-nSamples-blockSpacer] = self.matrix[:, nSamples+blockSpacer:]
            self.matrix[:, -nSamples:] = data
            self.matrix[:, -nSamples-blockSpacer:-nSamples] = (self.lowValue+self.highValue)/2

        
    def draw(self):
        self.canvas.restore_region(self.background)
        self.im.set_data( self.matrix)
        self.canvas.draw()
        
        
class  sound_viewer(object):
    
    def __init__(self, toSound, toResampledSound, logger, showtime=0.5, decimation=5, fs = 44100, ymin=-1000,  ymax=1000,*args, **kwargs):
        super(sound_viewer, self).__init__(*args, **kwargs)
        self.showtime=showtime*fs
        self.logger=logger
        toSound.riseConnection(self.logger)
        self.toSound=toSound.connection
        
        toResampledSound.riseConnection(self.logger)
        self.toResampledSound=toResampledSound.connection
        
        self.decimation=decimation
        self.xsound=np.arange(self.showtime)
        self.ysound=np.ones(*np.shape(self.xsound))
        self.xsample=np.arange(0,self.showtime,self.decimation)-296
        self.ysample=np.ones(*np.shape(self.xsample))
        self.ymin=ymin
        self.ymax=ymax
        
    def run(self):
        self.prerun()
        self.stayAlive = True
        cnt=0
        while self.stayAlive:
            
            hasNew = self.toSound.poll(25)
            
            if hasNew:
                soundChunk = self.toSound.recv()
                resampledChunk = self.toResampledSound.recv()
                self.update(soundChunk.data,
                            resampledChunk.data, 
                            0)#(resampledChunk.startTime-resampledChunk.alignment.includedPast- soundChunk.startTime+  soundChunk.alignment.includedPast-500))
                cnt=cnt+1
                self.show() 
                if(soundChunk.continuity==Continuity.last):
                    self.stayAlive=False
                    
            
            
                    
            if cnt==10:
                cnt=0
                if(sys.platform=='win32'):
                    plt.close('all')                
                    time.sleep(0.001)
                    plt.ion()
                    self.prerun()
                self.show() 
                
    def setupimage(self):
        plt.ioff()
        self.fig = plt.figure(figsize=(20,5))
        self.ax = self.fig.add_subplot(111)
        self.canvas = self.ax.figure.canvas
        self.background = self.canvas.copy_from_bbox(self.ax.get_figure().bbox)
        #self.ax.set_title('Sound and resampled sound')
        self.ax.set_ylim( self.ymin,self.ymax)
        self.ax.set_xlim(0,self.showtime)
        #self.ax.set_xlim(self.showtime-1639-60,self.showtime)
        #self.ax.set_xlim(-100,1639*1.2)
        self.ax.set_xlim(self.showtime*.6,self.showtime)
        
        
        self.pl1, =plt.plot(self.xsound , self.ysound , color='b', linestyle='-', linewidth=2.0)
        self.pl2, =plt.plot(self.xsample, self.ysample, color='r', linestyle='-', linewidth=2.0) 
        #self.pl3, =plt.plot(np.array([self.showtime-1639,self.showtime-1639]), np.array([-2000,2000]), color='r', linestyle='-', linewidth=2.0) 
        plt.show(block=False)
        self.canvas.draw()
        
        
    def prerun(self):
        
        self.setupimage()
    
    def update(self,sounddata,resampleddata, timeshift):
        nSoundSamples = np.shape(sounddata)[0]
        nSampleSamples = np.shape(resampleddata)[0]
        
        self.ysound[0:-nSoundSamples]=self.ysound[nSoundSamples:]
        self.ysound[-nSoundSamples:]=sounddata
        
        
        self.xsample=np.arange(0,self.showtime,self.decimation)+timeshift
        self.ysample[0:-nSampleSamples]=self.ysample[nSampleSamples:]
        self.ysample[-nSampleSamples:]=np.real(resampleddata)
        
        
    def show(self):

        self.canvas.restore_region(self.background)
        self.pl1.set_xdata(self.xsound)
        self.pl1.set_ydata(self.ysound)
        self.pl2.set_xdata(self.xsample)
        self.pl2.set_ydata(self.ysample)
        self.canvas.draw()
        
 
