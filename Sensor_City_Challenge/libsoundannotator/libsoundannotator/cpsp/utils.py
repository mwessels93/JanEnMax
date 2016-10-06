# -*- coding: u8 -*-

import scipy as sp
import numpy as np

def rat(x, tol=10**-12):
	""" returns a ratio approximation for x, with a maximum error of
	    the second argument, 10^-12 as default
	"""
	
	# store original value of x
	Xorg = x
	error = 0
	k = 0
	
	# mat= [n(k) n(k-1); d(k) d(k-1)]
	# first column contains current fraction n/k
	# second column contains fraction from previous iteration
	mat = np.matrix([[1,0],[0,1]])
	hist = np.matrix([[0],[0]])
	
	# While the error is too high
	# or if we haven't started yet
	while (error > tol and not x == 0 and k < 10) or k==0:
		
		# Only the first iteration we do not use the reciprocal of x
		if k > 0:
			x = 1/float(x)
			
		# Increase k and determine integer part of x
		k += 1
		d = round(x)
		
		# subtract the integer part of the float and represent the
		# remainder as 1/r
		x = x - d
		
		# save the history
		hist[:,0] = mat[:,0]
		
		# update the matrix
		mat[:,0] = mat*np.matrix([[d],[1]])
		mat[:,1] = hist
		
		# calculate the new error
		error = abs((float(mat[0,0])/float(mat[1,0])) - Xorg)

	p = mat[0,0]/np.sign(mat[1,0])
	q = abs(mat[1,0])	
	return p,q
		
