#!/usr/bin/env python3

# builtins
import argparse
import sys
import shutil

# my modules
import submerge.modules
from submerge.utils import get_docstring, AbsolutePath


def main(_args = None):
    # allow running through the command line
    if _args:
        if _args[0] != 'submerge':
           _args = ['submerge'] + _args
        sys.argv = _args

    # check for available modules
    available_modules = {name: getattr(submerge.modules, name) for name in submerge.modules.__all__}

    # root parser
    parser = argparse.ArgumentParser(prog='submerge')
    parser.add_argument('-v', '--verbose', action='store_true')

    # parent parser
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('path', help='A path to an mkv file, or a directory of files (default: %(default)s)', type=AbsolutePath, default='.', nargs='?')
    parent_parser.add_argument('-r', '--recursive', help='Recurse into directories', action='store_true')

    # add the subparsers
    subparsers = parser.add_subparsers(help='Module to use', dest='module')
    parsers = {mod: subparsers.add_parser(mod, parents=[parent_parser], description=get_docstring(available_modules[mod].Operator)) for mod in available_modules}

    # initialize all operators to properly load all argparse options
    # if we parse the options before loading the operators, the help messages will be missing all the module arguments
    operators = {mod: available_modules[mod].Operator(parsers[mod]) for mod in available_modules}

    # all modules loaded, let's actually parse our top-level options
    args = parser.parse_args()
    if not args.module:
        print('Please specify a module.')
        sys.exit(1)

    # any processing we need to do before running the module
    # check for mkvtoolnix
    mkvtoolnix = ['mkvmerge', 'mkvpropedit', 'mkvextract', 'mkvinfo']
    missing_mkvtoolnix = [exec for exec in mkvtoolnix if not shutil.which(exec)]
    if missing_mkvtoolnix:
        print(f"{', '.join(missing_mkvtoolnix)} not found.")

    # pass control to the specified module
    operator = operators[args.module]
    operator.process(parser)

