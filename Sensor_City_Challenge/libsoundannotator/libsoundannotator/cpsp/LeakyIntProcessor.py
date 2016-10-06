from libsoundannotator.streamboard               import processor
from libsoundannotator.streamboard.continuity    import Continuity
import time
from datetime import datetime, date, timedelta

import numpy as np
import os.path as path
import h5py
import os
import multiprocessing, logging

class LeakyIntProcessor(processor.Processor):
    '''

    '''

    periods={'week':7*24*60*60,'day':24*60*60,'hour':60*60,'minute':60,'second':1}
    statefile=None
    historyfile=None

    def __init__(self, boardConn, name,*args, **kwargs):
        super(LeakyIntProcessor, self).__init__(boardConn, name,*args, **kwargs)
        #set required keys to subscription keys, or to empty list
        self.requiredKeys = kwargs.get('requiredKeys', self.requiredKeys)
        self.requiredParameters( 'maxFileSize')
        self.requiredParametersWithDefault(
                            blockwidth=1,        # output blockwidth in seconds.
                            discountFactor=0.02, # daily discount factor
                            period='week',
                            shapes=dict(),      # scalar features don't need a shape, an extra dimension will be treated as instances belonging to consecutive blocks.
                            dtypes=dict(),
                            cachedir=path.join(path.expanduser('~'),'.sa'),
                            stateFillValue=np.nan
                        )
        self.discountFactor=self.config['discountFactor']
        self.setPhaseAndPeriod()

        self.LeakyIntData=dict()
        self.lastusedphaseindex=dict()
        '''
            Create cachedir if non-existent
        '''
        cachedir=self.config['cachedir']
        if not path.exists(cachedir):
            os.mkdir(cachedir)

        '''
            Shapes used internally are different than those specified as init command as period index is added as dimension. Therefore we calculate the shapes here.
        '''
        self.historyKeyShape=dict()
        self.historyKeyType=dict()
        for key in self.requiredKeys:
            if key in self.config['shapes'].keys():
                keyShape=(self.noofphases,)+self.config['shapes'][key]
                self.historyKeyShape[key]=(self.noofdayphases,)+self.config['shapes'][key]
            else:
                keyShape=(self.noofphases,)
                self.historyKeyShape[key]=(self.noofdayphases,)

            if key in self.config['dtypes'].keys():
                keyType=self.config['dtypes'][key]
            else:
                keyType=np.float
            self.historyKeyType[key]=keyType

            self.LeakyIntData[key]=np.zeros(keyShape,dtype=keyType)
            self.lastusedphaseindex[key]=-1
            new_statefile_created=self.checkStateFile(key)
            new_historyfile_created=self.checkHistoryFile(key)
            if (not new_historyfile_created) and new_statefile_created:
                self.calculateStateFromHistory()

    def prerun(self):
        super(LeakyIntProcessor, self).prerun()

    def processData(self, smartChunk):
        # for now just some snippets of usefull code not functional yet

        result=dict()
        valid = True

        for key in self.requiredKeys:
            average_key=key+'_average'
            index_key=key+'_index'
            diff_key=key+'_diff'
            data=smartChunk.received[key].data
            startTime=smartChunk.received[key].startTime
            
            
            if type( startTime) is type(''):
                self.logger.warning(' Invalid timestamp {}'.format( startTime))
                return
            
            noofsamples=data.shape[-1]
            if not noofsamples > 0 or np.any(np.isnan(data)) or np.any(np.isinf(data)):
                valid=False
                if noofsamples > 0:
                    self.continuity=Continuity.discontinuous
            else:
                result[key]=np.zeros(data.shape[:-1]+(noofsamples,))
                result[average_key]=np.zeros(data.shape[:-1]+(noofsamples,))
                result[index_key]=np.zeros(data.shape[:-1]+(noofsamples,))
                result[diff_key]=np.zeros(data.shape[:-1]+(noofsamples,))

                self.statefile = h5py.File(self.statefilename, 'a')
                for sample in np.arange(0,noofsamples):
                    if len(data.shape)==1:
                        self.updateHistoryFile(key,data[sample],startTime+self.blockwidth*sample)
                        result[diff_key][sample],result[average_key][sample],result[index_key][sample],result[key][sample]=self.updateStateFile(key,data[sample],startTime+self.blockwidth*sample)
                    elif  len(data.shape)==2:
                        self.updateHistoryFile(key,data[:,sample],startTime+self.blockwidth*sample)
                        result[diff_key][:,sample],result[average_key][:,sample],result[index_key][:,sample],result[key][:,sample]=self.updateStateFile(key,data[:,sample],startTime+self.blockwidth*sample)
                    elif  len(data.shape)==3:
                        self.updateHistoryFile(key,data[:,:,sample],startTime+self.blockwidth*sample)
                        result[diff_key][:,:,sample],result[average_key][:,:,sample],result[index_key][:,:,sample],result[key][:,:,sample]=self.updateStateFile(key,data[:,:,sample],startTime+self.blockwidth*sample)

                self.statefile.close()

        if not valid:
            result=None

        return result

    def checkHistoryFile(self,key):
        new_group_created=False

        cachedir=path.join(self.config['cachedir'],'history')
        if not path.exists(cachedir):
            os.mkdir(cachedir)

        self.historyfilename=path.join(self.config['cachedir'],'history','{}.{}'.format(self.name,'hdf')) # We need a random access format here. hdf seems better suited for this purpose than npz.
        self.historyfile = h5py.File(self.historyfilename, 'a')

        if not key in self.historyfile:
            self.historyfile.create_group(key)
            new_group_created=True

        self.historyfile.close()

        return new_group_created

    def checkStateFile(self,key):
        new_dataset_created=False

        statecachedir=path.join(self.config['cachedir'],'state')
        if not path.exists(statecachedir):
            os.mkdir(statecachedir)

        self.statefilename=path.join(self.config['cachedir'],'state','{}_{}.{}'.format(self.name,self.config['period'],'hdf')) # We need a random access format here. hdf seems better suited for this purpose than npz.
        self.statefile = h5py.File(self.statefilename, 'a')
        if not key in self.statefile:
            #self.statefile.create_group(key,self.LeakyIntData[key].shape,self.LeakyIntData[key].dtype)
            self.statefile.create_dataset(key,self.LeakyIntData[key].shape,self.LeakyIntData[key].dtype,fillvalue=self.config['stateFillValue'])
            self.statefile.create_dataset(key+'_ptcount',self.LeakyIntData[key].shape,self.LeakyIntData[key].dtype, fillvalue=self.config['stateFillValue'])
            new_dataset_created=True

        self.statefile.close()

        return new_dataset_created


    def updateHistoryFile(self,key,data,startTime):
        
        
        self.historyfile = h5py.File(self.historyfilename, 'a')

        dayperiod=self.dayperiod(startTime)
        dayindex=self.dayphase(startTime)
        dayperiodlist='/'.join([str(x) for x in (key,)+dayperiod])

        group=self.historyfile.require_group(dayperiodlist)
        dset=group.require_dataset('data',self.historyKeyShape[key],self.historyKeyType[key],fillvalue=np.nan)

        dset[dayindex]=data

        self.historyfile.close()


    def updateStateFile(self,key,data,startTime):

        if np.any(np.isnan(data)) or np.any(np.isinf(data)):
            return None

        phaseindex=self.phase(startTime)


        if phaseindex is self.lastusedphaseindex[key]:
            self.logger.error('phaseindex is used twice: {}'.format(phaseindex))

        dset=self.statefile.require_dataset(key,self.LeakyIntData[key].shape,self.LeakyIntData[key].dtype,fillvalue=np.nan)
        dset_ptcount=self.statefile.require_dataset(key+'_ptcount',self.LeakyIntData[key].shape,self.LeakyIntData[key].dtype,fillvalue=0)


        dset_ptcount[phaseindex]=dset_ptcount[phaseindex]+1
        if not np.any(np.isnan(dset[phaseindex])):
            averaging_factor=1.0/dset_ptcount[phaseindex]
            if np.all( averaging_factor > self.discountFactor):
                dset[phaseindex]=dset[phaseindex]*(1-averaging_factor)+averaging_factor*data
            else:
                dset[phaseindex]=dset[phaseindex]*(1-self.discountFactor)+self.discountFactor*data
        else:
            dset[phaseindex]=data
            dset_ptcount[phaseindex]=1

        self.lastusedphaseindex[key]=phaseindex
        return data-dset[phaseindex],dset[phaseindex],phaseindex, data

    def finalize(self):

        # Close all open storage files
        if self.statefile:
            self.statefile.flush()
            self.statefile.close()

        if self.historyfile:
            self.historyfile.flush()
            self.historyfile.close()

        super(LeakyIntProcessor, self).finalize()

    '''
        Depending on the choice of period calculate a tuple identifying the the period. The days in the last/first week of the year will be assigned to their year, potentially creating a split of a week over two years.
    '''

    def weekperiod(self,seconds):
        tstruct=time.localtime(seconds)
        tm_week=np.int(time.strftime('%U',tstruct)) # %U Week number of the year (Sunday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Sunday are considered to be in week 0.
        return tstruct.tm_year, tm_week

    def dayperiod(self,seconds):
        tstruct=time.localtime(seconds)
        tm_day=np.int(time.strftime('%w',tstruct))
        return  self.weekperiod(seconds)+(tm_day,)

    def hourperiod(self,seconds):
        tstruct=time.localtime(seconds)
        return self.dayperiod(seconds)+(tstruct.tm_hour,)

    def minuteperiod(self,seconds):
        tstruct=time.localtime(seconds)
        return self.hourperiod(seconds)+(tstruct.tm_min,)

    def secondperiod(self,seconds):
        tstruct=time.localtime(seconds)
        return self.minuteperiod(seconds)+(tstruct.tm_sec,)




    '''
        In calculating the phases taking seconds modulo 60 seconds creates a small error when leap seconds occur. Leap seconds being rare this is considered negligible.
    '''



    def weekphase(self,seconds):
        tstruct=time.localtime(seconds)
        tm_day=np.int(time.strftime('%w',tstruct))
        timeinperiod=tm_day*24*60*60+tstruct.tm_hour*60*60+tstruct.tm_min*60+tstruct.tm_sec%60+np.modf(seconds)[0]
        index = int(timeinperiod/self.blockwidth)
        return index

    def dayphase(self,seconds):
        tstruct=time.localtime(seconds)
        timeinperiod=tstruct.tm_hour*60*60+tstruct.tm_min*60+tstruct.tm_sec%60+np.modf(seconds)[0]
        index = int(timeinperiod/self.blockwidth)
        return index

    def hourphase(self,seconds):
        tstruct=time.localtime(seconds)
        timeinperiod=tstruct.tm_min*60+tstruct.tm_sec%60+np.modf(seconds)[0]
        index = int(timeinperiod/self.blockwidth)
        return index

    def minutephase(self,seconds):
        tstruct=time.localtime(seconds)
        timeinperiod=tstruct.tm_sec%60+np.modf(seconds)[0]
        index = int(timeinperiod/self.blockwidth)
        return index

    def secondphase(self,seconds):
        timeinperiod=np.modf(seconds)[0]
        index = int(timeinperiod/self.blockwidth)
        return index

    def setPhaseAndPeriod(self):
        self.phase_functions={  'week':self.weekphase,'day':self.dayphase,
                                'hour':self.hourphase,'minute':self.minutephase,
                                'second':self.secondphase}

        self.period_functions={ 'week':self.weekperiod,'day':self.dayperiod,
                                'hour':self.hourperiod,'minute':self.minuteperiod,
                                'second':self.secondperiod}

        self.blockwidth=self.config['blockwidth']
        self.periodduration=self.periods[self.config['period']]          # convert period to seconds
        self.phase=self.phase_functions[self.config['period']]          # select function to convert time to phase index < noofphases
        self.period=self.period_functions[self.config['period']]        # select function to convert time to a tuple indicating in which period a given time belongs.
        self.noofphases=self.periodduration/self.blockwidth
        self.noofdayphases=self.periods['day']/self.blockwidth

    def calculateStateFromHistory(self):
        '''
            Solution implemented here is not efficient but is robust and reuses code, as we don't expect to run this code often there is no point in full optimization.
        '''
        self.historyfile = h5py.File(self.historyfilename)
        self.statefile = h5py.File(self.statefilename)
        for key in self.requiredKeys:
            group=self.historyfile[key]
            for year in sorted(group.keys()):
                subgroup=group[year]
                for week in sorted(subgroup.keys() ):
                    subgroup2=subgroup[week]
                    for day in sorted(subgroup2.keys() ):
                        t_startofday = time.strptime('{} {} {}'.format(year, week ,day),'%Y %U %w')
                        t_startofday=time.mktime(t_startofday)
                        data=subgroup2[day]['data']
                        datasample=np.zeros(data.shape[1:])
                        for sample in np.arange(self.noofdayphases):
                            datasample[:,:]=data[sample,:,:]
                            self.updateStateFile(key,datasample,t_startofday+self.blockwidth*sample)

        self.statefile.close()
        self.historyfile.close()

    def getsamplerate(self,key):
        return 1/self.blockwidth
