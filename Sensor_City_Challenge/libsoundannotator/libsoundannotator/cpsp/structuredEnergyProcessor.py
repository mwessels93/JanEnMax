import os, time
import scipy.io
import numpy                    as np

# Streamboard architecture and processors
from libsoundannotator.streamboard.processor      import Processor, Continuity
from libsoundannotator.streamboard.continuity     import Continuity
from libsoundannotator.cpsp.structureProcessor    import structureProcessorCore
from libsoundannotator.cpsp.patchProcessor        import patchProcessorCore

# XML stuff
from xml.etree.ElementTree                   import ElementTree, Element, SubElement, Comment, tostring
import xml.etree.ElementTree    as ET


class structuredEnergyProcessor(Processor):
    requiredKeys=['E','f_tract','s_tract','f_pattern','s_pattern']
    intermediateKeys=['TfGate','TsGate','']
    resultKeys=['pulse','tone','noise','energy']
    
    def __init__(self,boardConn, name,*args, **kwargs):
        super(structuredEnergyProcessor, self).__init__(boardConn, name,*args, **kwargs)
        self.requiredParameters('SampleRate','globalOutputPathModifier','baseOutputDir','cli','svnBranch','svnversion')
        self.requiredParametersWithDefault(noofscales=100, 
                            TfThreshold=60, TfSlope=0.2,
                            TsThreshold=60, TsSlope=0.2,
                            split=[],NumpyOut=False,
                            MatlabOut=False, 
                            MatricesOut=True,
                            blockwidth=0.005,  # output blockwidth in seconds.
                            )
        
        self.TfThreshold=self.config['TfThreshold']
        self.TsThreshold=self.config['TsThreshold']
        self.TfSlope=self.config['TfSlope']
        self.TsSlope=self.config['TsSlope']
        
        self.fs=self.config['SampleRate']
        
        
        if self.config['blockwidth']*self.config['SampleRate'] < 1:
            #print('Blockwidth set to 1')
            self.blockwidth=1 # Internal blockwidth is in samples external in seconds.
        else:
            self.blockwidth=int(np.ceil(self.config['blockwidth']*self.config['SampleRate']))
        
        self.config['blockwidth']=self.blockwidth/self.config['SampleRate']
        
        self.resetblockbuffer()
        
            
        self.invokestr=self.config['cli']
        self.svnBranch=self.config['svnBranch']
        self.svnversion=self.config['svnversion']
        self.svnversion=self.svnversion.replace(':','-')
        
        
        
        self.PathModifier='{0}-{1}'.format(self.config['globalOutputPathModifier'],
            time.strftime('%Y-%m-%d-%H-%M'))
        
        self.resultspath=os.path.join(self.config['baseOutputDir'],self.PathModifier)
        if not os.path.exists(self.resultspath):
            os.makedirs(self.resultspath)
        
        self.xmlmetafilename_relative='PSA_MetaData.xml'
        self.xmlmetafilename=os.path.join(self.resultspath,self.xmlmetafilename_relative)
        
        self.logmsg['info'].append('XMLMETAFILE: {0}'.format(self.xmlmetafilename))
        
        
        self.numpyout=self.config['NumpyOut']
        self.matlabout=self.config['MatlabOut']
        self.matricesout=self.config['MatricesOut']
        
        npzfilepath=None
        self.npzdatadir='npzdata'
        if self.numpyout:
            npzfilepath=os.path.join(self.resultspath,self.npzdatadir)
            
            if not os.path.exists(npzfilepath):
                os.makedirs(npzfilepath)
        
        matfilepath=None
        self.matdatadir='matdata'
        if  self.matlabout:
            matfilepath=os.path.join(self.resultspath,self.matdatadir)
        
            if not os.path.exists(matfilepath):
                os.makedirs(matfilepath)
        
        self.noofbands=len(self.config['split'])-1
        self.xmldatadir='xml'
        xmlfilepath=os.path.join(self.resultspath,self.xmldatadir)
        os.makedirs(xmlfilepath)   
        
        self.logmsg['info'].append('Path to Numpy data: {0} , Path to Matlab data: {1}'.format(npzfilepath, matfilepath))
        
        
    def prerun(self):
        super(structuredEnergyProcessor,self).prerun()
        self.logger.info('self.blockwidth: {0}'.format(self.blockwidth))
        self.xmlmetafile=open(self.xmlmetafilename,'w+')
        self.xmlmetaroot=Element('PSA_Collection')
        self.xmlmetatree=ElementTree(self.xmlmetaroot)
        meta   = SubElement(self.xmlmetaroot,'meta')
        invocation=SubElement(meta,'invocation')
        invocation.text=self.invokestr
        branch=SubElement(meta,'branch')
        branch.text=self.svnBranch
        svnversion=SubElement(meta,'svnversion')
        svnversion.text=self.svnversion
        self.xmlmetatree.write(self.xmlmetafile)
        self.xmlmetafile.close()
        
    def finalize(self):
        super(structuredEnergyProcessor,self).finalize()
        
    def getInputs(self):
        for subscription in self.inConn:
            new = subscription.connection.poll(self.timeout)
            if new:
                chunk = subscription.connection.recv()
                self.logger.info('number {0} continuity {1}  key {2}'.format(chunk.number ,chunk.continuity, subscription.receiverKey) )
                self.smartCompositeChunk.inject(subscription.receiverKey, chunk)
        
    def processData(self, data):
        
        result=None
        
        # empty buffer if chunks are discontinuous
        if data.chunkcontinuity < Continuity.withprevious:
            self.resetblockbuffer()
        
        if not data.chunkcontinuity == Continuity.last:
            # Generate xml output
            if data.chunkcontinuity==Continuity.newfile or data.chunkcontinuity == Continuity.discontinuous:
                self.createnewSingleSourceXMLfile(data)
           
                
            self.logger.warning("Chunk continuity is {0}".format(Continuity.getstring(Continuity, data.chunkcontinuity)))  
            result=self.writeSingleSourceXMLfile(data)
            
        return result
        
    def resetblockbuffer(self):
        self.blockbuffer=dict()
        for key in self.requiredKeys:
            self.blockbuffer[key]=np.zeros((self.config['noofscales'],0))
    
    def bandmeans(self, data, split, keeptime=False):
        splitdata=np.split(data,split)
        splitdata=splitdata[1:-1] # Throw away invalid first and last band
        bandmeans=[]
        
        for view in splitdata:
            if keeptime :
                viewmean=np.mean(view,axis=0)
            else:
                viewmean=np.mean(view)
                
            bandmeans.append(viewmean)
       
        return np.log(np.array(bandmeans))
       
    def createnewSingleSourceXMLfile(self,data):
        name='PSA'
        for source in data.sources:
            dummy, sourcename=os.path.split(source)
            sourcename=sourcename.replace('.','_')
            name='_'.join( [name,sourcename])
        
        self.xmlfilename=os.path.join(self.resultspath,self.xmldatadir,'{0}.xml'.format(name))
        self.logger.info('___________ NEW FILE ____________{0}'.format(self.xmlfilename))
        self.xmlfile=open(self.xmlfilename,'w+')
        self.xmlroot=Element('PSA_SingleSource')
        self.xmlmetadata=SubElement(self.xmlroot, 'xmlmetadatafile')
        self.xmlmetadata.text=self.xmlmetafilename_relative
        self.xmltree=ElementTree(self.xmlroot)
        self.xmltree.write(self.xmlfile)
        self.xmlfile.close()
        self.xmlmetatree=ET.parse(self.xmlmetafilename)
        self.xmlmetaroot=self.xmlmetatree.getroot()
        singlesource=SubElement(self.xmlmetaroot,'singlesource')
        singlesource.text=os.path.join(self.xmldatadir,'{0}.xml'.format(name))
        self.xmlmetatree.write(self.xmlmetafilename)
        self.xmltree=ET.parse(self.xmlfilename)
    
    
    def writeSingleSourceXMLfile(self, data):
        result=None
        
        
        noofsamples=dict()
        noofnewsamples=dict()
        noofoldsamples=dict()
        newbuffersize=dict()
          
        for key in self.requiredKeys:
            noofnewsamples[key]=np.shape(data.received[key].data)[1]
            noofoldsamples[key]=np.shape(self.blockbuffer[key])[1]
            noofsamples[key]=noofnewsamples[key]+noofoldsamples[key]
            
        noofsampleslist= [ noofsamples[key]  for key in self.requiredKeys] 
        noofcompletesamples=min(noofsampleslist) 
        #noofcompletesamples=min(noofsamples.items(), key=lambda x: x[1]) 
        noofblocks=int(np.floor(noofcompletesamples/self.blockwidth))
        

        for key in self.requiredKeys:
            newbuffersize[key]=noofsamples[key]-noofblocks*self.blockwidth
        
        currentdata=dict()
        for key in self.requiredKeys:
            self.logger.info('key: {0} shape buffer: {1} shape input: {2}'.format(key,np.shape(self.blockbuffer[key]),np.shape(data.received[key].data)))
            currentdata[key]=np.concatenate((self.blockbuffer[key],data.received[key].data), axis=1)
            self.blockbuffer[key]=currentdata[key][:,noofsamples[key]-newbuffersize[key]:noofsamples[key]]
         
       
            
        if noofblocks > 0:
            self.xmlroot=self.xmltree.getroot()
            chunk = SubElement(self.xmlroot,'chunk', chunkno='{0:d}'.format(data.number))
            
            if (self.numpyout or self.matlabout) and self.matricesout:  
                self.savematrices(noofblocks,currentdata,data.number,chunk)
    
            self.writexmlchunk(data, chunk, noofblocks, noofoldsamples)
            
            if self.numpyout or self.matlabout:  
                result=self.writeblockstofile(noofblocks,chunk,currentdata,data.number)
            else:
                result=self.writexmlblocks(noofblocks,chunk,currentdata)
            
            self.xmltree.write(self.xmlfilename)
            self.logger.info(tostring(chunk))
        
        return result
        
    def writexmlchunk(self, data,chunk, noofblocks, noofoldsamples):
        sources=SubElement(chunk,'sources')
        
        for element in data.sources:
            source=SubElement(sources,'source')
            source.text=element
        
       
        _noofblocks  = SubElement(chunk, 'noofblocks')
        _noofblocks.text ='{0:d}'.format(noofblocks)
        
        _noofblocks  = SubElement(chunk, 'blockwidth')
        _noofblocks.text ='{0:d}'.format(self.blockwidth)
               
        samplerate  = SubElement(chunk, 'samplerate')
        samplerate.text ='{0:d}'.format(data.received['E'].fs)
        
        continuity  = SubElement(chunk, 'continuity')
        
        
        continuity.text = Continuity.getstring(Continuity,data.continuity)
        
        starttime  = SubElement(chunk, 'starttime')
        
        if( data.continuity == Continuity.withprevious):
            starttime.text = str(data.startTime- data.alignment.includedPast/data.received['E'].fs- noofoldsamples['E']/data.received['E'].fs)
        elif data.chunkcontinuity == Continuity.withprevious:
            starttime.text = str(data.startTime)
        else:
            starttime.text = str(data.startTime + data.alignment.droppedAfterDiscontinuity/data.received['E'].fs)
        
       
        
        
    def writexmlblocks(self,blocks,noofblocks,chunk,currentdata):        
        result=dict()
        bandmeans=SubElement(chunk,'bandmeans')
        
        for blockindex in np.arange(noofblocks,dtype='int'):
            blockno='{0:d}'.format(blockindex)
            _block= SubElement(bandmeans, 'block', blockno=blockno)
            
            E=currentdata['E'][:,blockindex*self.blockwidth:(blockindex+1)*self.blockwidth]
            Tf=currentdata['f_tract'][:,blockindex*self.blockwidth:(blockindex+1)*self.blockwidth]
            Ts=currentdata['s_tract'][:,blockindex*self.blockwidth:(blockindex+1)*self.blockwidth]
            
            TfGate=(1+np.tanh( (Tf-self.TfThreshold)*self.TfSlope ) )/2
            TsGate=(1+np.tanh( (Ts-self.TsThreshold)*self.TsSlope ) )/2
           
            result['P']=self.bandmeans(E*TfGate, self.config['split'] )
            result['T']=self.bandmeans(E*TsGate, self.config['split'] )
            result['N']=self.bandmeans(E*(1-TfGate)*(1-TsGate), self.config['split'])
            result['E']=self.bandmeans(E, self.config['split'])
   
            noise  = SubElement(_block, 'noise')
            noise.text=np.savetext(result['N']) #''.join(['{0:.2f},'.format(num) for num in result['N']])
            
            pulse = SubElement(_block, 'pulse')
            pulse.text=''.join(['{0:.2f},'.format(num) for num in result['P']])
           
            tone = SubElement(_block, 'tone')
            tone.text=''.join(['{0:.2f},'.format(num) for num in result['T']])
            
            energy = SubElement(_block, 'energy')
            energy.text=''.join(['{0:.2f},'.format(num) for num in result['E']])
            
        return result         
        
    def writeblockstofile(self,noofblocks,chunk,currentdata,number):        
        result=dict()
        bandmeans=SubElement(chunk,'bandmeans')
        
        result['P']=np.zeros((self.noofbands,noofblocks))
        result['T']=np.zeros((self.noofbands,noofblocks))
        result['N']=np.zeros((self.noofbands,noofblocks))
        result['E']=np.zeros((self.noofbands,noofblocks))
        
        for blockindex in np.arange(noofblocks,dtype='int'):            
            E=currentdata['E'][:,blockindex*self.blockwidth:(blockindex+1)*self.blockwidth]
            Tf=currentdata['f_tract'][:,blockindex*self.blockwidth:(blockindex+1)*self.blockwidth]
            Ts=currentdata['s_tract'][:,blockindex*self.blockwidth:(blockindex+1)*self.blockwidth]
            
            TfGate=(1+np.tanh( (Tf-self.TfThreshold)*self.TfSlope ) )/2
            TsGate=(1+np.tanh( (Ts-self.TsThreshold)*self.TsSlope ) )/2
           
            result['P'][:,blockindex]=self.bandmeans(E*TfGate, self.config['split'] )
            result['T'][:,blockindex]=self.bandmeans(E*TsGate, self.config['split'] )
            result['N'][:,blockindex]=self.bandmeans(E*(1-TfGate)*(1-TsGate), self.config['split'])
            result['E'][:,blockindex]=self.bandmeans(E, self.config['split'])
   
        if self.numpyout:
            self.numpyoutrelative=os.path.join(self.npzdatadir,'vEA_{0:010d}.npz'.format(number))
            self.numpyfilename=os.path.join(self.resultspath,self.numpyoutrelative)            
            np.savez(self.numpyfilename,result)
            savednumpydata  = SubElement(chunk, 'npz_vEA_file')
            savednumpydata.text = self.numpyoutrelative
        
        if self.matlabout:
            self.matlaboutrelative=os.path.join(self.matdatadir,'vEA_{0:010d}.mat'.format(number))
            self.matlabfilename=os.path.join(self.resultspath,self.matlaboutrelative)      
            scipy.io.savemat(self.matlabfilename, result)
            savedmatlabdata  = SubElement(chunk, 'mat_vEA_file')
            savedmatlabdata.text = self.matlaboutrelative
            
        return result         
            
        
    def savematrices(self,noofblocks,currentdata,number,chunk):
        blocks=dict()
        for key in self.requiredKeys:
            self.logger.warning('Key is: {0} and shape: {1}'.format(key, np.shape(currentdata[key])))
            newblockdata=np.zeros((self.config['noofscales'],noofblocks))
            for blockindex in np.arange(noofblocks,dtype='int'):
                newblockdata[:,blockindex]=np.max(currentdata[key][:,blockindex*self.blockwidth:(blockindex+1)*self.blockwidth],axis=1)
            blocks[key]=newblockdata
            
        if self.numpyout:
            self.numpyoutrelative=os.path.join(self.npzdatadir,'tracts_{0:010d}.npz'.format(number))
            self.numpyfilename=os.path.join(self.resultspath,self.numpyoutrelative)            
            np.savez(self.numpyfilename,blocks)
            savednumpydata  = SubElement(chunk, 'npzfilename')
            savednumpydata.text = self.numpyoutrelative
        
        if self.matlabout:
            self.matlaboutrelative=os.path.join(self.matdatadir,'tracts_{0:010d}.mat'.format(number))
            self.matlabfilename=os.path.join(self.resultspath,self.matlaboutrelative)      
            scipy.io.savemat(self.matlabfilename, blocks)
            savedmatlabdata  = SubElement(chunk, 'matlabfilename')
            savedmatlabdata.text = self.matlaboutrelative
