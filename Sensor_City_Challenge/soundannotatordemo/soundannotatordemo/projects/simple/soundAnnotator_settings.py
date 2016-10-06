import numpy as np
import os 

settings = {
    'receiverkey' : 'dataout',
    'maxFileSize' : 104857600, #in bytes
    'location' : os.path.join(os.path.expanduser('~'),'data','libsoundannotator','hdfdump_location'),
    'ptnreferencevalue' : 0.0, # Assume split [10,60] , blockwidth=0.005, fs=44100, 20/np.log(10)*np.log10(2/(50*44100*0.005/25)) 
}
