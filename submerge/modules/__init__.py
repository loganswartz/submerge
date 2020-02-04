#!/usr/bin/env python3

# builtins
import pathlib as _pathlib
import inspect as _inspect

# get all the python modules in this directory
_directory = _pathlib.Path(_inspect.getframeinfo(_inspect.currentframe()).filename).resolve().parent
_files = _directory.glob('**/*.py')

_blacklist = ['<stdin>', '__init__.py', '__main__.py', '_template.py']

# add all files to __all__ except for this __init__.py
__all__ = [module.stem for module in _files if module.is_file() and module.name not in _blacklist]

# import all modules under the module namespace
from . import *

