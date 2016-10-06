# -*- coding: u8 -*-
import numpy as np

import pygame.mixer as sndMixer
import pygame.sndarray as sndArray
import time
import pyaudio

def playSound(data, fs, format=-16, nchannels=1):
    """ Plays a sound from an array. Comparable with Matlab soundsc routine """
    
    # Initialize the pygame mixer
    sndMixer.pre_init(fs, format, nchannels)
    sndMixer.init()
    
    # Calculate the length of the sound in seconds
    timeout = len(data)/float(fs)

    # Make sure the data is a numpy array
    sndArray.use_arraytype('numpy')
    soundArray = np.array(data)
    
    # Create a pygame.Sound object
    sound = sndArray.make_sound(soundArray)
    
    # Play the sound and wait until it is played fully
    sound.play()
    time.sleep(timeout)
    
	
