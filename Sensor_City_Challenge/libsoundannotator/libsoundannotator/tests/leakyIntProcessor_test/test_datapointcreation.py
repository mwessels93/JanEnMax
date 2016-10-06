'''
    Experimental testing code starts here
'''
from nose import with_setup

from libsoundannotator.cpsp.LeakyIntProcessor import LeakyIntProcessor
import numpy as np
import os.path as path
import multiprocessing, logging
import os
import shutil
import h5py 
import time


logger = multiprocessing.log_to_stderr()

datadir=path.join(path.expanduser('~'),'soundannotator_data')
if not os.path.exists(datadir):
    os.mkdir(datadir)

from chunks import smartCompositeChunk, initialSmartCompositeChunk, DataChunk
    
class EmptyProcessor(object):
    name='dummy'
    previousClaimNumber=-1
    
    def __init__(self, *args, **kwargs):
        self.requiredKeys = kwargs.get('requiredKeys')
        self.shape = kwargs.get('shape')
        self.logger = multiprocessing.log_to_stderr()
        #self.logger.setLevel(logging.CRITICAL)
        self.smartCompositeChunk=initialSmartCompositeChunk(self.requiredKeys, -1, self)
        self.sources=set([self.name])
        
        for key in self.requiredKeys:
            self.smartCompositeChunk.received[key]=DataChunk(data=np.ones(self.shape), 
            startTime=1449478633.333646, 
            fs=44500, 
            processorName=self.name, 
            sources=self.sources)
        
    
    def claim(self, smartCompositeChunk, callingchunk):
        self.previousClaimNumber=callingchunk.number
        self.smartCompositeChunk=smartCompositeChunk



        
def my_setup_function():
    global cachedir, timezone
    
    if 'TZ' in os.environ:
        timezone=os.environ['TZ']
    else:
        timezone=None
    os.environ['TZ'] = 'Europe/Amsterdam'
    
    cachedir=path.join(path.expanduser('~'),'soundannotator_data','libsoundannotator_test')
    
    
def my_teardown_function():
    global cachedir, timezone
    if not timezone is None:
        os.environ['TZ'] = timezone
    elif 'TZ' in os.environ:
        del os.environ['TZ']
    time.tzset()
    
    if path.exists(cachedir):
        shutil.rmtree(cachedir)
    pass


@with_setup(my_setup_function, my_teardown_function)        
def test_historyfilecreation():
    '''
        Assure historyfile gets created
    ''' 
    processorname='S2S_LIP_Test'
    global cachedir
    blockwidth=0.1
    LIP=LeakyIntProcessor(None,processorname,logdir='~',requiredKeys=['feature1','feature2'], cachedir=cachedir, maxFileSize=np.power(2,24),period='minute',blockwidth=blockwidth)
    
    LIP.logger=logger
    dummyprocessor=EmptyProcessor(requiredKeys=['feature1','feature2'],shape=(1,))
           
    filename=path.join(cachedir,'history','{}.{}'.format(processorname,'hdf')) 
    historyfile = h5py.File(filename, 'r')
    del LIP
    
@with_setup(my_setup_function, my_teardown_function)        
def test_historygroupcreation():
    '''
        Assure groups in historyfile get created, one group for each required key
    ''' 
    processorname='S2S_LIP_Test'
    global cachedir
    blockwidth=0.1
    requiredKeys=['feature1','feature2']
    LIP=LeakyIntProcessor(None,processorname,logdir='~',requiredKeys=requiredKeys, cachedir=cachedir, maxFileSize=np.power(2,24),period='minute',blockwidth=blockwidth)
    
    LIP.logger=logger
    dummyprocessor=EmptyProcessor(requiredKeys=requiredKeys,shape=(1,))
           
    filename=path.join(cachedir,'history','{}.{}'.format(processorname,'hdf')) 
    historyfile = h5py.File(filename, 'r')
    for key in requiredKeys:
        assert key in historyfile.keys()
    del LIP

@with_setup(my_setup_function, my_teardown_function)        
def test_statefilecreation():
    '''
        Assure statefile gets created
    ''' 
    processorname='S2S_LIP_Test'
    global cachedir
    blockwidth=0.1
    period='minute'
    LIP=LeakyIntProcessor(None,processorname,logdir='~',requiredKeys=['feature1','feature2'], cachedir=cachedir, maxFileSize=np.power(2,24),period=period,blockwidth=blockwidth)
    
    LIP.logger=logger
    dummyprocessor=EmptyProcessor(requiredKeys=['feature1','feature2'],shape=(1,))
           
    filename=path.join(cachedir,'state','{0}_{1}.{2}'.format(processorname,period,'hdf')) 
    historyfile = h5py.File(filename, 'r')
    del LIP
    
    
@with_setup(my_setup_function, my_teardown_function)        
def test_stategroupcreation():
    '''
         Assure groups in statefile get created, one group for each required key
    ''' 
    processorname='S2S_LIP_Test'
    global cachedir
    blockwidth=0.1
    requiredKeys=['feature1','feature2']
    period='minute'
    LIP=LeakyIntProcessor(None,processorname,logdir='~',requiredKeys=requiredKeys, cachedir=cachedir, maxFileSize=np.power(2,24),period=period,blockwidth=blockwidth)
    
    LIP.logger=logger
    dummyprocessor=EmptyProcessor(requiredKeys=requiredKeys,shape=(1,))
    
    filename=path.join(cachedir,'state','{0}_{1}.{2}'.format(processorname,period,'hdf'))
    statefile = h5py.File(filename, 'r')
    for key in requiredKeys:
        assert key in statefile.keys()
    del LIP

@with_setup(my_setup_function, my_teardown_function)        
def test_datapointcreation():
    '''
        Test initialization and updating for 1d-timeseries
    ''' 
    processorname='S2S_LIP_Test'
    global cachedir
    blockwidth=0.1
    requiredKeys=['feature1','feature2']
    shape=(1,)
    noofsamples=100
    period='minute'
    
    LIP=LeakyIntProcessor(None,processorname,logdir='~',requiredKeys=requiredKeys, cachedir=cachedir, maxFileSize=np.power(2,24),period=period,blockwidth=blockwidth)
    LIP.logger=logger
    dummyprocessor=EmptyProcessor(requiredKeys=requiredKeys,shape=shape)
    
    startTimes=dict()
    for key in requiredKeys:
        startTimes[key]=dummyprocessor.smartCompositeChunk.received[key].startTime
    
    for index2 in np.arange(0,3,1):
        for index in np.arange(0,noofsamples,1):       
            LIP.processData(dummyprocessor.smartCompositeChunk)
            for key in requiredKeys:
                dummyprocessor.smartCompositeChunk.received[key].startTime+=blockwidth
        for key in requiredKeys:
            startTimes[key]+=60
            dummyprocessor.smartCompositeChunk.received[key].startTime=startTimes[key]
    filename=path.join(cachedir,'history','{}.{}'.format(processorname,'hdf')) 
    historyfile = h5py.File(filename, 'r')
    test_array=np.ones((noofsamples+2,))
    test_array[0]=np.nan
    test_array[-1]=np.nan
    for key in requiredKeys:
        np.testing.assert_equal(historyfile[key]['2015']['49']['1']['data'][358332:358332+noofsamples+2],test_array)
        np.testing.assert_equal(historyfile[key]['2015']['49']['1']['data'][358932:358932+noofsamples+2],test_array)
        np.testing.assert_equal(historyfile[key]['2015']['49']['1']['data'][359532:359532+noofsamples+2],test_array)
    historyfile.close()
        
    filename=path.join(cachedir,'state','{0}_{1}.{2}'.format(processorname,period,'hdf')) 
    statefile = h5py.File(filename, 'r')
    for key in requiredKeys:
        np.testing.assert_equal(statefile[key][132:132+noofsamples+2],test_array)
    statefile.close()
    del LIP

@with_setup(my_setup_function, my_teardown_function) 
def test_multidatapointcreation():
    '''
        Test initialization and updating for 1d-timeseries, multisamples at a time
    ''' 
    processorname='S2S_LIP_Test'
    global cachedir
    blockwidth=0.1
    requiredKeys=['feature1','feature2']
    shape=(1,10)
    noofchunks=10
    noofsamples=noofchunks*shape[1]
    period='minute'
    
    LIP=LeakyIntProcessor(None,processorname,logdir='~',requiredKeys=requiredKeys, cachedir=cachedir, maxFileSize=np.power(2,24),period=period,blockwidth=blockwidth)
    
    LIP.logger=logger
    dummyprocessor=EmptyProcessor(requiredKeys=requiredKeys,shape=shape)
    
    for index in np.arange(0,noofchunks,1):
        for index2 in np.arange(0,3,1):
            LIP.processData(dummyprocessor.smartCompositeChunk)
        for key in requiredKeys:
            dummyprocessor.smartCompositeChunk.received[key].startTime+=10*blockwidth
        
    filename=path.join(cachedir,'history','{}.{}'.format(processorname,'hdf')) 
    historyfile = h5py.File(filename, 'r')
    test_array=np.ones((noofsamples+2,))
    test_array[0]=np.nan
    test_array[-1]=np.nan
    for key in requiredKeys:
        np.testing.assert_equal(historyfile[key]['2015']['49']['1']['data'][358332:358332+noofsamples+2],test_array)
    historyfile.close()
        
    filename=path.join(cachedir,'state','{0}_{1}.{2}'.format(processorname,period,'hdf')) 
    statefile = h5py.File(filename, 'r')
    for key in requiredKeys:
        np.testing.assert_equal(statefile[key][132:132+noofsamples+2],test_array)
    statefile.close()
    del LIP


@with_setup(my_setup_function, my_teardown_function) 
def test_multidatapointcreation2d():
    '''
        Test initialization and updating for 2d-timeseries, multisamples at a time
    ''' 
    processorname='S2S_LIP_Test'
    global cachedir
    blockwidth=0.1
    requiredKeys=['feature1','feature2']
    shape=(2,3,10)
    noofchunks=10
    noofsamples=noofchunks*shape[-1]
    shapes={'feature1':(2,3,),'feature2':(2,3,)}
    period='minute'
    
    LIP=LeakyIntProcessor(None,processorname,logdir='~',requiredKeys=requiredKeys, cachedir=cachedir, maxFileSize=np.power(2,24),period=period,blockwidth=blockwidth,shapes=shapes)
    
    LIP.logger=logger
    dummyprocessor=EmptyProcessor(requiredKeys=requiredKeys,shape=shape)

    
    for index in np.arange(0,noofchunks,1):
        for index2 in np.arange(0,3,1):
            LIP.processData(dummyprocessor.smartCompositeChunk)
        for key in requiredKeys:
            dummyprocessor.smartCompositeChunk.received[key].startTime+=10*blockwidth
     
    filename=path.join(cachedir,'history','{}.{}'.format(processorname,'hdf')) 
    historyfile = h5py.File(filename, 'r')
    test_array=np.ones((noofsamples+2,)+(2,3,))
    test_array[0,:,:]=np.nan
    test_array[-1,:,:]=np.nan
    for key in requiredKeys:
        np.testing.assert_equal(historyfile[key]['2015']['49']['1']['data'][358332:358332+noofsamples+2,:,:],test_array)
    historyfile.close()

    filename=path.join(cachedir,'state','{0}_{1}.{2}'.format(processorname,period,'hdf')) 
    statefile = h5py.File(filename, 'r')
    for key in requiredKeys:
        np.testing.assert_equal(statefile[key][132:132+noofsamples+2,:,:],test_array)
    statefile.close()
    del LIP


@with_setup(my_setup_function, my_teardown_function)
def test_restoreHistory():
    '''
        Test initialization and updating for 2d-timeseries, multisamples at a time
    ''' 
    processorname='S2S_LIP_Test'
    global cachedir
    blockwidth=60
    requiredKeys=['feature1','feature2']
    shape=(2,3,10)
    noofchunks=10
    noofsamples=noofchunks*shape[-1]
    shapes={'feature1':(2,3,),'feature2':(2,3,)}
    period='hour'
    
    LIP=LeakyIntProcessor(None,processorname,logdir='~',requiredKeys=requiredKeys, cachedir=cachedir, maxFileSize=np.power(2,24),period=period,blockwidth=blockwidth,shapes=shapes)
    
    LIP.logger=logger
    dummyprocessor=EmptyProcessor(requiredKeys=requiredKeys,shape=shape)
    
    startTime=dict()
    for key in requiredKeys:
        startTime[key]=dummyprocessor.smartCompositeChunk.received[key].startTime
    
    for index in np.arange(0,noofchunks,1):
        for index2 in np.arange(0,3,1):
            # Generate time stamps small interval on 3 consecutive days  
            for key in requiredKeys:
                dummyprocessor.smartCompositeChunk.received[key].data*=0.8
                dummyprocessor.smartCompositeChunk.received[key].startTime=startTime[key]+shape[-1]*blockwidth*index+index2*24*3600
            LIP.processData(dummyprocessor.smartCompositeChunk)
    
    filename=path.join(cachedir,'state','{0}_{1}.{2}'.format(processorname,period,'hdf')) 
    f=h5py.File(filename,'r')
    li_data=f['feature1'] 
    f.close()
    
    shutil.rmtree(path.join(cachedir,'state'))
    LIP.statefile=None
    
    for key in requiredKeys:
        LIP.checkStateFile(key)
            
    LIP.calculateStateFromHistory()
    
    
    f=h5py.File(filename,'r')
    
    li_data2=f['feature1'] 
    f.close()
    
    np.testing.assert_equal(li_data,li_data2)
