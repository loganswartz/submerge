#!/usr/bin/env python3

# builtins
import pathlib
import argparse
import sys

# my modules
import submerge.modules
from submerge.utils import get_docstring, AbsolutePath


def main():
    # check for available modules
    available_modules = {name: getattr(submerge.modules, name) for name in submerge.modules.__all__}

    # root parser
    parser = argparse.ArgumentParser(prog='submerge')
    parser.add_argument('-v', '--verbose', action='store_true')

    # parent parser
    dir_parser = argparse.ArgumentParser(add_help=False)
    dir_parser.add_argument('-d', '--dir', help='A directory containing mkv files', type=AbsolutePath, default='.')

    # add the subparsers
    subparsers = parser.add_subparsers(help='Module to use', dest='module')
    parsers = {mod: subparsers.add_parser(mod, parents=[dir_parser], description=get_docstring(available_modules[mod].Operator)) for mod in available_modules}

    # initialize all operators to properly load all argparse options
    # if we parse the options before loading the operators, the help messages will be missing all the module arguments
    operators = {mod: available_modules[mod].Operator(parsers[mod]) for mod in available_modules}

    # all modules loaded, let's actually parse our top-level options
    args = parser.parse_args()
    if not args.module:
        print('Please specify a module.')
        sys.exit(1)

    # any processing we need to do before running the module

    # pass control to the specified module
    operator = operators[args.module]
    operator.process(parser)

