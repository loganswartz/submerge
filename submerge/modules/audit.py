#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor
import time
import itertools
import collections
from typing import NamedTuple, Any
import pathlib

from submerge.utils import pretty_time_delta, get_metadata, get_files, get_track_pattern, get_docstring


class TestResult(NamedTuple):
    passed: bool
    info: Any

    def __bool__(self):
        return self.passed


class FileResult(NamedTuple):
    file: pathlib.Path
    tests: list


def get_test_func_name(func):
    func_name = func.__name__.replace('_test_', '')
    words = [word.strip().lower() for word in func_name.split('_') if word.strip()]
    name = [word[0].upper() + word[1:] for word in words]
    return ' '.join(name)


class AuditOperator(object):
    """
    Scan a directory and audit all the files in it, noting any issues that could be fixed.
    """
    def __init__(self, subparser):
        subparser.add_argument('-t', '--timed', help='Report the time taken to audit', action='store_true')
        subparser.add_argument('-p', '--pattern', help='Produce a pattern that can be used with the \'tracks\' module', action='store_true')
        subparser.add_argument('-f', '--format', choices=['category', 'individual'], default='category')

    @property
    def tests(self):
        tests = {}
        for attr in dir(self):
            if '_test_' in attr:
                func = getattr(self, attr)
                name = get_docstring(func) or get_test_func_name(func)
                tests[name] = func
        return tests

    def process(self, parser):
        # parse args
        self.args = parser.parse_args()

        if self.args.timed:
            self.start_time = time.perf_counter()

        files = get_files(self.args.path, self.args.recursive)

        # process files
        with ThreadPoolExecutor() as executor:
            results = executor.map(self.check_file, files)

        self.report(results, format=self.args.format)

    def check_file(self, file):
        if self.args.verbose:
            print(f"Checking {file.relative_to(self.args.path)}....")
        try:
            metadata = get_metadata(file)
        except KeyError:
            print(f'ERROR: {file} could not be read.')
            return

        # perform tests
        tests = {name: test(file, metadata) for name, test in self.tests.items()}

        return FileResult(file, tests)

    def _test_pattern(self, file, metadata):
        if not self.args.pattern:
            return TestResult(True, None)

        pattern = get_track_pattern(metadata)

        # sort by track number, then by track type
        pattern.sort(key=lambda entry: entry[0])
        track_ordering = {'v': 1, 'a': 2, 's': 3}
        pattern.sort(key=lambda entry: track_ordering[entry[1]])

        return TestResult(False, ':'.join([f"{track}{type}" for (track, type) in pattern]))

    def _test_improperly_ordered_tracks(self, file, metadata):
        pattern = get_track_pattern(metadata)

        # sort by track number, then by track type
        pattern.sort(key=lambda entry: entry[0])
        track_ordering = {'v': 1, 'a': 2, 's': 3}
        pattern.sort(key=lambda entry: track_ordering[entry[1]])

        properly_ordered = [int(track) for track, type in pattern] == sorted([int(track) for track, type in pattern])

        # convert pattern to pretty string
        tracks = [f"{track}{type}" for track, type in pattern]
        pattern_string = ':'.join(tracks)

        return TestResult(properly_ordered, pattern_string)

    def _test_undefined_tracks(self, file, metadata):
        undefined_tracks = []
        try:
            for track in metadata['tracks']:
                if track['type'] in ['subtitles', 'audio'] and track['properties']['language'] == 'und':
                    undefined_tracks.append(track['properties']['number'])
        except KeyError:
            print(f"ERROR: {file} could not be read, data may be incorrect")

        return TestResult(not bool(undefined_tracks), undefined_tracks)

    def report(self, results, format = 'category'):
        results = list(results)
        if not results:
            print('No files found.')
            return

        # filter out any files where there aren't any positive tests
        results = [result for result in results if not all(result.tests.values())]
        if self.args.pattern:
            results = [FileResult(file, {'Pattern': tests.get('Pattern')}) for file, tests in results]

        # sort by filename
        results.sort(key=lambda entry: entry.file)

        if len(results) == 0:
            print('No problems found.')
        else:
            if format == 'individual':
                for file, tests in results:
                    filename = file.relative_to(self.args.path)
                    print(f"{filename}:")
                    for test, passed in tests.items():
                        if not passed:
                            print(f"    {test}: {passed}")
            elif format == 'category':
                final = collections.defaultdict(list)
                for file, tests in results:
                    for test, passed in tests.items():
                        if not passed:
                            final[test].append((file, passed))

                for test, items in final.items():
                    print(f"{test}:")
                    for file, result in items:
                        filename = file.relative_to(self.args.path)
                        print(f"    {result.info} - {filename}")

        if self.args.timed:
            time_elapsed = pretty_time_delta(time.perf_counter() - self.start_time)
            print(f"Time elapsed: {time_elapsed}")


Operator = AuditOperator

