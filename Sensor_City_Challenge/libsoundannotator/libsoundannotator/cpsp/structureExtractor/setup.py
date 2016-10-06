from distutils.core import setup, Extension
import sys
import numpy
import os  
import shutil
'''
To builds the python extension the StructureExtractor module run setup.py:
python setup.py build_ext --inplace

For installation:
python setup.py build install --prefix=<local package dir>

or with debugging info
python setup.py build --debug install --prefix=<local package dir>

extra_link_args for windows are based on: http://bugs.python.org/issue4431
'''

swig_command='swig -c++ -python -I{0} -o structureExtractor_wrap.cpp  structureExtractor.i'.format(os.path.join('..','framescaleArray'))
os.system(swig_command)

shutil.copy('structureExtractor.py','..')

if sys.platform.startswith('win'):
    extra_link_args=['/MANIFEST']
else:
    extra_link_args=[]
    
include_dirs =[numpy.get_include(),os.path.join('..','framescaleArray')]  
    
moduleStructureExtractor=Extension('_structureExtractor', 
					sources=['structureExtractor_wrap.cpp',
					'structureExtractor.cpp',os.path.join('..','framescaleArray','framescaleArray.cpp'),
					'fsArrayCorrelator.cpp',
					'thresholdCrossing.cpp',
					'pasCalculator.cpp',
					'textureCalculator.cpp'],
					extra_link_args=extra_link_args,
					include_dirs =include_dirs,
					)

setup(name='structureExtractor', 
		version='1.0', 
		description='This is a demo', 
		ext_modules=[moduleStructureExtractor],
		py_modules=['structureExtractor'],
		)

