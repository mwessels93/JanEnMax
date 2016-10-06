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
    if 'TZ' in os.environ:
        timezone=os.environ['TZ']
    else:
        timezone=None
    os.environ['TZ'] = 'Europe/Amsterdam'
    time.tzset()
    
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
 
@with_setup(my_setup_function, my_teardown_function)      
def test_weekphase():
    LIP=LeakyIntProcessor(None,'S2S_LIP_Test',logdir='~',requiredKeys=['empty','emptytoo'], cachedir=cachedir, maxFileSize=np.power(2,24),period='minute',blockwidth=0.1)
    np.testing.assert_equal( LIP.weekphase(1449478633.333646), 1222333) 
    del LIP
 
@with_setup(my_setup_function, my_teardown_function)      
def test_dayphase():
    LIP=LeakyIntProcessor(None,'S2S_LIP_Test',logdir='~',requiredKeys=['empty','emptytoo'], cachedir=cachedir, maxFileSize=np.power(2,24),period='minute',blockwidth=0.1)
    np.testing.assert_equal( LIP.dayphase(1449478633.333646), 358333)
    del LIP
 
@with_setup(my_setup_function, my_teardown_function)  
def test_hourphase():
    LIP=LeakyIntProcessor(None,'S2S_LIP_Test',logdir='~',requiredKeys=['empty','emptytoo'], cachedir=cachedir, maxFileSize=np.power(2,24),period='minute',blockwidth=0.1)
    np.testing.assert_equal( LIP.hourphase(1449478633.333646), 34333)  
    del LIP  
 
@with_setup(my_setup_function, my_teardown_function)  
def test_minutephase():
    LIP=LeakyIntProcessor(None,'S2S_LIP_Test',logdir='~',requiredKeys=['empty','emptytoo'], cachedir=cachedir, maxFileSize=np.power(2,24),period='minute',blockwidth=0.1)
    np.testing.assert_equal( LIP.minutephase(1449478633.333646), 133) 
    del LIP   
 
@with_setup(my_setup_function, my_teardown_function)  
def test_secondphase():
    LIP=LeakyIntProcessor(None,'S2S_LIP_Test',logdir='~',requiredKeys=['empty','emptytoo'], cachedir=cachedir, maxFileSize=np.power(2,24),period='minute',blockwidth=0.1)
    np.testing.assert_equal( LIP.secondphase(1449478633.333646), 3)
    del LIP

