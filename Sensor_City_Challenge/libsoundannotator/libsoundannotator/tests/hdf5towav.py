import h5py, sys, numpy as np, scipy.io.wavfile as wavfile, os

f = sys.argv[1]

try:
	handle = h5py.File(f, 'r')
except Exception as e:
	print e
	sys.exit(1)

sound = np.array(handle['sound'])
fs = 44100

print sound.shape, sound.dtype
wavfile.write('sound.wav', fs, sound)

