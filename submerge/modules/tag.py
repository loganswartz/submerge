#!/usr/bin/env python3

# Imports {{{
# builtins
from concurrent.futures import ThreadPoolExecutor
import logging
import subprocess

# 3rd party
import click

# this module
from submerge.modules.base import path_args
from submerge.utils import get_files, language, quote_cmd

# }}}


log = logging.getLogger(__name__)

# TODO
# @click.option('-u', '--only-undefined', help='Only modify tracks when they are undefined', is_flag=True)
# @click.option('-c', '--confirm', help='Ask for confirmation before processing', is_flag=True)


@click.command()
@path_args
@click.option(
    "-l",
    "--language",
    help="Set the language of a track",
    metavar="TRACK LANGUAGE",
    type=(int, language),
    nargs=2,
    required=True,
)
@click.option(
    "-s",
    "--simulate",
    help="Print out the command to be executed instead of actually executing it",
    is_flag=True,
)
def tag(paths, recursive, language, simulate):
    """
    Modify the track attributes of a given file.
    """

    files = get_files(paths, recursive)
    track, lang = language

    with ThreadPoolExecutor() as executor:
        results = executor.map(
            lambda file: edit_track(file, track, language=lang, simulate=simulate),
            files,
        )

    log.debug("Command outputs:")
    for output in results:
        log.debug(output)

    if not simulate:
        log.info("All files modified.")


def edit_track(file, track, simulate=False, **kwargs):
    cmd = ["mkvpropedit", str(file.expanduser().resolve()), "--edit", f"track:@{track}"]
    for key, value in kwargs.items():
        cmd.extend(["--set", f"{key}={value.alpha_3}"])

    if simulate:
        log.info(quote_cmd(cmd))
        return cmd
    else:
        return subprocess.check_output(cmd, text=True)
