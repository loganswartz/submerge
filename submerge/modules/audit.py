#!/usr/bin/env python3

# Imports {{{
# builtins
import collections
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import logging
import pathlib
import time
from typing import Iterable, NamedTuple, Any, Optional

# 3rd party
import click

# local modules
from submerge.modules.base import path_args
from submerge.utils import (
    pretty_time_delta,
    get_metadata,
    get_files,
    get_track_pattern,
    get_docstring,
)

# }}}


log = logging.getLogger(__name__)


class TestResult(NamedTuple):
    passed: bool
    info: Any

    def __bool__(self):
        return self.passed


class FileResult(NamedTuple):
    file: pathlib.Path
    tests: Optional[dict]


@click.command()
@path_args
@click.option(
    "-t",
    "--timed",
    help="Report the time taken to audit",
    is_flag=True,
)
@click.option(
    "-p",
    "--pattern",
    help="Produce a pattern that can be used with the 'tracks' module",
    is_flag=True,
)
@click.option(
    "-f",
    "--format",
    help="Method that should be used to organize results",
    type=click.Choice(["category", "individual"]),
    default="category",
    show_default=True,
)
def audit(paths, recursive, timed, pattern, format):
    """
    Find issues in the given files and report them.
    """

    # parse args
    if timed:
        start_time = time.perf_counter()

    files = get_files(paths, recursive)

    # process files
    results = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(partial(check_file, pattern=pattern), file) for file in files]
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except TypeError as e:
                log.error(e)

    def report(results: Iterable[FileResult], pattern, format="category"):
        if not results:
            log.info("No files found.")
            return

        # filter out any files where there aren't any positive tests
        results = [result for result in results if not all(result.tests.values())]
        if pattern:
            results = [
                FileResult(file, {"Pattern": tests.get("Pattern")})
                for file, tests in results
            ]

        # sort by filename
        results.sort(key=lambda entry: entry.file)

        if len(results) == 0:
            log.info("No problems found.")
        else:
            if format == "individual":
                for file, tests in results:
                    # filename = file.relative_to(pathlib.Path.cwd())
                    log.info(f"{file.name}:")
                    for test, passed in tests.items():
                        if not passed:
                            log.info(f"    {test}: {passed.info}")
            elif format == "category":
                final = collections.defaultdict(list)
                for file, tests in results:
                    for test, passed in tests.items():
                        if not passed:
                            final[test].append((file, passed))

                for test, items in final.items():
                    log.info(f"{test}:")
                    for file, result in items:
                        # filename = file.relative_to(pathlib.Path.cwd())
                        log.info(f"    {result.info} - {file.name}")

        if timed:
            time_elapsed = pretty_time_delta(time.perf_counter() - start_time)
            log.info(f"Time elapsed: {time_elapsed}")


    report(results, pattern, format=format)


def tests():
    def get_test_func_name(func):
        func_name = func.__name__.replace("_test_", "")
        words = [word.strip().lower() for word in func_name.split("_") if word.strip()]
        name = [word[0].upper() + word[1:] for word in words]
        return " ".join(name)

    return {
        get_docstring(func) or get_test_func_name(func): func
        for name, func in globals().items()
        if name.startswith("_test_")
    }


def check_file(file, pattern):
    log.debug(f"Checking {file.name}....")
    try:
        metadata = get_metadata(file)
    except KeyError:
        log.error(f"ERROR: {file} could not be read.")
        return FileResult(file, None)

    # perform tests
    results = {name: test(file, metadata, pattern) for name, test in tests().items()}

    return FileResult(file, results)


def _test_pattern(file, metadata, pattern):
    if not pattern:
        return TestResult(True, None)

    track_pattern = get_track_pattern(metadata)

    # sort by track number, then by track type
    track_pattern.sort(key=lambda entry: entry[0])
    track_ordering = {"v": 1, "a": 2, "s": 3}
    track_pattern.sort(key=lambda entry: track_ordering[entry[1]])

    return TestResult(False, ":".join([f"{track}{type}" for (track, type) in track_pattern]))


def _test_improperly_ordered_tracks(file, metadata, pattern):
    track_pattern = get_track_pattern(metadata)

    # sort by track number, then by track type
    track_pattern.sort(key=lambda entry: entry[0])
    track_ordering = {"v": 1, "a": 2, "s": 3}
    track_pattern.sort(key=lambda entry: track_ordering[entry[1]])

    properly_ordered = [int(track) for track, _ in track_pattern] == sorted(
        [int(track) for track, _ in track_pattern]
    )

    # convert pattern to pretty string
    tracks = [f"{track}{type}" for track, type in track_pattern]
    pattern_string = ":".join(tracks)

    return TestResult(properly_ordered, pattern_string)


def _test_undefined_tracks(file, metadata, pattern):
    undefined_tracks = []
    try:
        for track in metadata["tracks"]:
            if (
                track["type"] in ["subtitles", "audio"]
                and track["properties"]["language"] == "und"
            ):
                undefined_tracks.append(track["properties"]["number"])
    except KeyError:
        log.info(f"ERROR: {file} could not be read, data may be incorrect")

    return TestResult(not bool(undefined_tracks), undefined_tracks)
