import numpy as np
import math

delta_time = 1
tau = 6.
FBR_SCOPE= np.array([-10,10]) 
FBR_RANGE= np.array([-20,20]) 

step = 0.3           		



noiseSTD=3.

FBR_values = np.arange(FBR_RANGE[0],FBR_RANGE[1],step)

indLow = [(idx,val) for idx,val in zip(range(len(FBR_values)),FBR_values) if val > -noiseSTD][0][0]

print indLow

indHigh= [(idx,val) for idx,val in zip(range(len(FBR_values)),FBR_values) if val > noiseSTD][0][0]

print indHigh

col1 = np.linspace(FBR_SCOPE[0],0, indLow)
col2 = np.linspace(0,0,indHigh-indLow)
col3 = np.linspace(0,FBR_SCOPE[1],401-indHigh)

print col1.shape
print col2.shape
print col3.shape

FBR_cor = np.power(10,(0.1*np.bmat('col1 col2 col3')))
loss = np.power(math.e, (-delta_time/(np.transpose(FBR_cor) * tau)))

print loss.shape

E = np.random.random_sample((10,100))

history = np.zeros((E.shape[0],E.shape[1]),dtype='float')

fbr = np.subtract(E,history) #subtract entire array to get FBR matrix
fbr = np.clip(fbr, FBR_SCOPE[0], FBR_SCOPE[1]) #limit entire matrix using clipping function

#compute loss lookup indices
#lookup contains one corresponding loss index for each value in fbr matrix, in the same matrix shape
#so if fbr:
#[1 2 3]
#[0 4 5]
#[9 5 3]
# then lookup takes the same shape, with floored int values:
#[i i i]
#[i i i]
#[i i i]
losslookup = np.floor((fbr - FBR_SCOPE[0])/.3).astype(int) + 1
#from the lookup, we create another same shaped matrix with the values of the loss matrix,
#indicated by the indices of the lookup matrix
#numpy can do that by 'inserting' the newly shaped matrix with indices into the original one.
#it takes only the values in 'loss' from the indices of 'lookup' and returns the new shape-value combination matrix
#We do have to reshape the array as it has become a 3D array with z=1, because of python's array nesting
BG_loss = np.reshape(loss[losslookup],(losslookup.shape[0],losslookup.shape[1]))

BG = np.multiply(history,BG_loss) + np.multiply(E,(1 - BG_loss))

#save current BG response into history
history = BG

print BG
