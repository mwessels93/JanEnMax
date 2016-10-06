# -*- coding: u8 -*-

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.image import NonUniformImage

def cochleogram(EdB, fs, dRange=(-10,60)):
    """ Plot a cochleogram from EdB data. Scale time
        axis using fs (Hz). 

        Dynamical range can be set using a tuple (min,max)
        or a list [min, max]
        Returns handles for the figure and the axis

    """

    drMin = np.min(dRange)
    drMax = np.max(dRange)

    # Flip and normalize EdB
    normEdB = np.flipud(EdB.T)
    EdB[EdB > drMax] = drMax
    EdB[EdB < drMin] = drMin

    x = np.linspace(0,np.shape(normEdB)[1]/fs,np.shape(normEdB)[1])
    y = np.linspace(1,np.shape(normEdB)[0],np.shape(normEdB)[0])

    fig = plt.figure(figsize=(10,4))
    ax = fig.add_subplot(111)
    im = NonUniformImage(ax, interpolation='nearest', 
    extent=(0,np.shape(normEdB)[1]/fs,1,np.shape(normEdB)[0]))
    im.set_data(x,y,normEdB)
    ax.images.append(im)
    ax.set_xlim(0,np.shape(normEdB)[1]/fs)
    ax.set_ylim(1,np.shape(normEdB)[0])
    ax.set_xlabel('time (s)')
    ax.set_ylabel('cochlear segments')
    ax.set_title('Cochleogram')
    plt.show()






