import numpy as np


class fftw(object):
    
    def __init__(self):
        pass
        
    def importsingle(self):
        import fftw3f
        self.fftw=fftw3f

    def importdouble(self):
        import fftw3 
        self.fftw=fftw3 

    def fftw_plan(self):
        pass
         
    fftwtype={
        np.float32:importsingle,
        np.complex64:importsingle,
        np.float64:importdouble,
        np.complex128:importdouble, 
    }

    fftw_fdomain_type={
        importsingle:np.complex64,
        importdouble:np.complex128,
    }

    def importfftw(self,dTypeIn,dTypeOut):
        
        if not (dTypeIn in self.fftwtype and dTypeOut in self.fftwtype ):
            raise(TypeError('No fftw3 module available for the combination {0} with output {1}'.format(dTypeIn,dTypeOut) )) 
            
        if(self.fftwtype[dTypeIn]==self.fftwtype[dTypeOut]):
            self.fftwtype[dTypeIn](self)
        else:
            raise(TypeError('No fftw3 module available for the combination {0} with output {1}'.format(dTypeIn,dTypeOut) )) 

        return self.fftw_fdomain_type[self.fftwtype[dTypeIn]]
        

if __name__ == '__main__':
    myfftw=fftw()
    myfftw.importfftw(np.float32,np.float32)
    myfftw.importfftw(np.float32,np.complex64)
    myfftw.importfftw(np.float64,np.complex128)
    
    try:
        myfftw.importfftw(np.float64,np.complex64)
        print('Error')
    except TypeError as t:
        print t
       
    try:
        myfftw.importfftw(np.int64,np.complex64)
        print('Error')
    except TypeError as t:
        print t
    
    FDomainType=myfftw.importfftw(np.float32,np.float32)
    print 'fftw_fdomain_type: {0}'.format(FDomainType)
    
