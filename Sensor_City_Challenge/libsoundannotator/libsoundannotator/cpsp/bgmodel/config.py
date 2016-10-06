def getDefaults(tau, subtract=None, mask=None, **kwargs):
	return {
		'FBR_scope': kwargs.get('fbr_scope', [-5, 5]),
		'FBR_range': kwargs.get('fbr_range', [-200, 200]),
		'delta_time': kwargs.get('delta_time', .005), #seconds
		'tau': tau, #seconds
		'noiseSTD': kwargs.get('noise_std', 3.),
		'step': kwargs.get('step', .3),
		'subtract': subtract,
        'mask':mask
	}

defaults = getDefaults(0.0)

def tau(t, end):
	while t < end:
		t *= 2
		yield t

def defmodels(t,end):
	defaultmodels = [getDefaults(t) for t in tau(t, end)]
	return defaultmodels
