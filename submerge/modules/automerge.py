#!/usr/bin/env python3

# Imports {{{
# builtins
import logging
import pathlib

# 3rd party
import click

# local modules
from submerge.modules.base import path_args

# }}}


log = logging.getLogger(__name__)


@click.command(hidden=True)
@path_args
@click.option('-s', '--subtitles', help='A directory containing subtitles', metavar='DIR', type=pathlib.Path, default='.')
def automerge(paths, recursive, subtitles):
    """
    Automerge subtitles into their matching video files.

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
    log.info(subtitles)
