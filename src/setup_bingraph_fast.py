from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import numpy as np

ext_modules = [Extension("bingraph_fast",
                         sources=["bingraph_fast.pyx"],
                         include_dirs=[np.get_include()])]

setup(
  name = 'bingraph FAST',
  cmdclass = {'build_ext': build_ext},
  ext_modules = ext_modules
)
