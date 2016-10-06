# -*- coding: u8 -*-

import numpy as np
import matplotlib.pyplot as plt


def simpleWavePlot(data, fs):
    """ Very simple waveform plotter """
    data = np.array(data)
    if len(np.shape(data)) > 1:
		raise ValueError('simpleWavePlot only supports 1D arrays')
		
    nSamples = len(data)
    tmax = nSamples / float(fs)

    t = np.arange(0,tmax,1/float(fs))

    plt.plot(t, data)

    plt.xlabel('time (s)')
    plt.title('Plotted wave form')
    plt.show()
