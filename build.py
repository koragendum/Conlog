from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy

sourcefiles = ['conlog/solver_bindings.pyx', 'conlog/solver_c_fast.c']

def build(setup_kwargs):
    extensions = cythonize(sourcefiles) #  raw_extensions, include_path = [numpy.get_include()])
    setup_kwargs.update({
        'ext_modules': extensions,
    })
