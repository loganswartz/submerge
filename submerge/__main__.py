#!/usr/bin/env python3

# builtins
import pathlib
import argparse

# my modules
import submerge.modules


# check for available modules
available_modules = {name: getattr(submerge.modules, name) for name in submerge.modules.__all__}

# root parser
parser = argparse.ArgumentParser(prog='submerge')
parser.add_argument('-v', '--verbose', action='store_true')

# parent parser
dir_parser = argparse.ArgumentParser(add_help=False)
dir_parser.add_argument('-d', '--dir', help='A directory containing mkv files', metavar='<path>', type=pathlib.Path, default='.')

def get_docstring(obj):
    lines = [line.strip() for line in obj.__doc__.split('\n') if line.strip()]
    return lines[0]

# add the subparsers
subparsers = parser.add_subparsers(help='Module to use', dest='module')
parsers = {mod: subparsers.add_parser(mod, parents=[dir_parser], description=get_docstring(available_modules[mod].Operator)) for mod in available_modules}

# initialize all operators to properly load all argparse options
# if we parse the options before loading the operators, the help messages will be missing all the module arguments
operators = {mod: available_modules[mod].Operator(parsers[mod]) for mod in available_modules}

# all modules loaded, let's actually parse our top-level options
args = parser.parse_args()

# any processing we need to do before running the module

# pass control to the specified module
operator = operators[args.module]
operator.process(parser)

