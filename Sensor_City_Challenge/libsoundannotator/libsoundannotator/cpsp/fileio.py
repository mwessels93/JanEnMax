# -*- coding: u8 -*-
import scipy.io.wavfile as wavio
    
def readwav(wavfile):
    """ Merely wrapper around scipy function 
        returns data, fs in Matlab-order
    """
    fs,data = wavio.read(wavfile)
    return data,fs
    
def writewav(wavfile,data,fs):
    """ Wrapper around scipy function """
    
    wavio.write(wavfile,fs,data)        
