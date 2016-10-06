from nose import with_setup

from libsoundannotator.cpsp.LeakyIntProcessor import LeakyIntProcessor
import numpy as np
import os.path as path
import shutil
import os, time

datadir=path.join(path.expanduser('~'),'soundannotator_data')
if not os.path.exists(datadir):
    os.mkdir(datadir)


def my_setup_function():
    global cachedir, timezone
    
    cachedir=path.join(path.expanduser('~'),'soundannotator_data','libsoundannotator_test')
   
    if 'TZ' in os.environ:
        timezone=os.environ['TZ']
    else:
        timezone=None
    os.environ['TZ'] = 'Europe/Amsterdam'
    time.tzset()
    
 
def my_teardown_function():
    global cachedir, timezone
    if not timezone is None:
        os.environ['TZ'] = timezone
    elif 'TZ' in os.environ:
        del os.environ['TZ']
    time.tzset()
    if path.exists(cachedir):
        shutil.rmtree(cachedir)

 
@with_setup(my_setup_function, my_teardown_function)    
def test_secondperiod():
    LIP=LeakyIntProcessor(None,'S2S_LIP_Test',logdir='~',requiredKeys=['empty','emptytoo'], cachedir=cachedir, maxFileSize=np.power(2,24),period='minute',blockwidth=0.1)
    np.testing.assert_equal( LIP.secondperiod(1449478633.333646), (2015, 49, 1, 9, 57, 13))
    del LIP
