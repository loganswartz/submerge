#!/usr/bin/env python3

# builtins
import pathlib
import argparse


class MergeOperator(object):
    """
    Merges subtitles into their matching video files.

    This operation works on a given directory containing mkv files. Based on
    those mkv files, it searches for potentially matching subtitle files in
    the same directory, child directories, or a specified alternative
    directory.

    There are 3 methods used to locate a subtitle file, and a failure to
    locate a file results in deferment to the next viable method:
        1. Searching for an exact filename match (with subtitle extension)
        2. Searching for a subtitle file with the same 'S__E__' qualifier
        3. Searching for a filename match with at least 75% similarity

    If a match is found, a subprocess call to 'mkvmerge' is initiated, and the
    files are merged. If an error occurs or there is no match, the error is
    logged and the operation continues on the next file.
    """
    def __init__(self, subparser):
        subparser.add_argument('-s', '--subtitles', help='A directory containing subtitles',  metavar='<path>', type=pathlib.Path, default='.')

    def process(self, parser):
        args = parser.parse_args()
        print(args)


# Alias the operator for easy retrieval
Operator = MergeOperator

