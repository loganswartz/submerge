#!/usr/bin/env python3

# Imports {{{
# builtins
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from functools import partial
import logging
import subprocess

# 3rd party
import click

# local modules
from submerge.modules.base import path_args
from submerge.utils import get_files, get_metadata, quote_cmd

# }}}


log = logging.getLogger(__name__)


@click.command()
@path_args
@click.option("-n", "--new-order", help="The new desired track ordering", required=True)
@click.option(
    "-p",
    "--pattern",
    help="Only modify a file if it matches the specified track pattern",
)
@click.option(
    "--strict", help="Only match a file if it matches the pattern exactly", is_flag=True
)
@click.option(
    "-s",
    "--simulate",
    help="Print out the command to be executed instead of actually executing it",
    is_flag=True,
)
def tracks(paths, recursive, new_order, pattern, strict, simulate):
    """
    Reorder the tracks of a file.

    If the --strict flag is not passed, any pattern that is a subset of the
    track ordering of a file will match that file. AKA, if a file has an ordering
    of 1v:2a:3s:4s, and you pass a pattern of 1v:2a:3s, that will match by default
    because the entire pattern can fit within the existing track ordering.
    """
    files = get_files(paths, recurse=recursive)

    if not files:
        log.info("No files found.")
        return

    results = {"pass": [], "fail": []}
    for file in files:
        if not pattern or (pattern and test(file, pattern, strict=strict)):
            results["pass"].append(file)
        else:
            results["fail"].append(file)

    results["pass"].sort()
    results["fail"].sort()

    if pattern:
        log.info("The following files matched the pattern:")
        for file in results["pass"]:
            log.info(f"    {file.name}")
        log.debug('The following files did not match the pattern:')
        for file in results['fail']:
            log.debug(f"    {file.name}")

        click.confirm("\nContinue?", abort=True)

    # process files
    with ThreadPoolExecutor() as executor:
        processed = executor.map(
            partial(modify_track, new_order=new_order, simulate=simulate),
            results["pass"],
        )

    return processed


def modify_track(file, new_order, simulate):
    cmd = ["mkvpropedit", str(file)]
    for old, new in enumerate(new_order.split(":"), 1):
        cmd += ["--edit", f"track:@{old}", "--set", f"track-number={new}"]

    if simulate:
        log.info(quote_cmd(cmd))
        return cmd
    else:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE)
        return proc


def test(file, pattern, strict=True):
    class TrackType(Enum):
        video = "v"
        audio = "a"
        subtitles = "s"

    user_pairings = {int(pair[0]): TrackType(pair[1]) for pair in pattern.split(":")}

    try:
        metadata = get_metadata(file)
        real_pairings = {
            int(track["properties"]["number"]): TrackType[track["type"]]
            for track in metadata["tracks"]
        }
    except KeyError:
        log.info(f"ERROR: {file} failed to be read.")
        return False

    # check if user_pairings is a subset of real_pairings
    if strict:
        matches = (
            len(user_pairings) == len(real_pairings)
            and user_pairings.items() == real_pairings.items()
        )
    else:
        matches = user_pairings.items() <= real_pairings.items()

    return matches
