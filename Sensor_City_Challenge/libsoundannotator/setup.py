from setuptools import setup, find_packages, Extension
from distutils.util import get_platform
import os, sys
import numpy as np

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# Generate meta-data for Git
from libsoundannotator.config.generateMetaData import generateMetaData
generateMetaData()

if sys.platform.startswith('win'):
    extra_link_args=['/MANIFEST']
else:
    extra_link_args=[]
ext_modules = []
structureExtractor_path = os.path.join('libsoundannotator','cpsp', 'structureExtractor')
patchExtractor_path = os.path.join('libsoundannotator','cpsp', 'patchExtractor')
framescaleArray_path= os.path.join('libsoundannotator','cpsp', 'framescaleArray')
io_path = os.path.join('libsoundannotator','io')
include_dirs =[np.get_include(),structureExtractor_path,patchExtractor_path,framescaleArray_path, io_path]
ext_modules.append(
                    Extension('_structureExtractor',
                                sources=[os.path.join(structureExtractor_path, fname) for fname in
                                    ('structureExtractor_wrap.cpp',
                                    'structureExtractor.cpp',
                                    'fsArrayCorrelator.cpp',
                                    'thresholdCrossing.cpp',
                                    'pasCalculator.cpp',
                                    'textureCalculator.cpp',)]+
                                    [os.path.join(framescaleArray_path, fname2) for fname2 in
                                    ('framescaleArray.cpp',)],
                                extra_link_args=extra_link_args,
                                include_dirs =include_dirs,
                            )
                )

ext_modules.append(
                    Extension('_patchExtractor',
                                sources=[os.path.join(patchExtractor_path, fname) for fname in
                                    ('patchExtractor_wrap.cpp',
                                    'patchExtractor.cpp',)]+
                                    [os.path.join(framescaleArray_path, fname2) for fname2 in
                                    ('framescaleArray.cpp',)],
                                extra_link_args=extra_link_args,
                                include_dirs =include_dirs,
                            )
                )

if __name__ == "__main__":
    setup(
        name='libSoundAnnotator',
        version='1.1',
        url='http://www.soundappraisal.eu',
        description='Package for online sound classification ',
        long_description=read('README'),
        author='Ronald van Elburg, Coen Jonker, Arryon Tijsma',
        author_email='r.a.j.van.elburg@soundappraisal.eu',
        download_url='--tba--',
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'Intended Audience :: Science/Research/Education',
            'License :: Other/Proprietary License',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python/C++',
            'Topic :: Scientific/Engineering :: Computational Auditory Scene Analysis'
        ],
        install_requires=[
            'numpy>=1.8.0',
            'scipy>=0.13.0',
            'pyaudio>=0.2.7',
            'nose>=1.3.1',
            'setproctitle>=1.0.1',
            'psutil>=0.4.1',
            'h5py>=2.3.0',
            'PyFFTW3>=0.2.1',
            'lz4>=0.7.0',
            'redis>=2.10.1',
            'oauthlib>=2.0.0',
        ],
        packages=find_packages(),
        ext_modules = ext_modules,
        ext_package = 'libsoundannotator.cpsp',
        test_suite='nose.collector',

        package_dir={
            'libsoundannotator.tests.structureExtractor_test': os.path.join('libsoundannotator','tests','structureExtractor_test')
        },
        package_data={
            'libsoundannotator.tests.structureExtractor_test': ['*.txt'],
        }
    )
