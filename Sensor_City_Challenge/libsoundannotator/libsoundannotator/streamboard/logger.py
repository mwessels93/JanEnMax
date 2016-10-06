'''
Unify calls to logger under windows and linux. Multiprocessing 
logger fails under windows, to make some level of logging available 
it is redericted to stdout.
'''
import multiprocessing
import logging
import sys, os

def new(reattach=False, level=logging.WARNING):
    
    if(reattach==True and not (sys.platform=='win32')):
        return
        
    if(sys.platform=='win32'):
        return  win_logger(level)
    else:
        return multiprocessing.get_logger()
            
class win_logger(object):
    
    def __init__(self,level=0):
        self.level=level
        
    def setLevel(self,level):
        self.level=level

    def info(self,info):
        if(self.level <= logging.INFO):
            print('[INFO]: {0}' .format(info))
            
    def warning(self,warning):
        if(self.level <= logging.WARNING):
            print('[WARNING]: {0}' .format(warning)) 
               
    def debug(self,debug):
        if(self.level <= logging.DEBUG):
            print('[DEBUG]: {0}'.format(debug))
            
    def error(self,error):
        if(self.level <= logging.ERROR):
            print('[DEBUG]: {0}'.format(error))
            
    def fatal(self,fatal):
        if(self.level <= logging.FATAL):
            print('[FATAL]: {0}' .format(fatal))

    def critical(self,critical):
        if(self.level <= logging.CRITICAL):
            print('[CRITICAL]: {0}' .format(critical))
