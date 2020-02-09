#!/usr/bin/env python3

import pathlib
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor
import time
from submerge.utils import pretty_time_delta
import itertools


class AuditOperator(object):
    """
    Scan a directory and audit all the files in it, noting any issues that could be fixed.
    """
    def __init__(self, subparser):
        subparser.add_argument('-r', '--recursive', help='Recurse into directories', action='store_true')
        subparser.add_argument('-t', '--timed', help='Report the time taken to audit', action='store_true')

    def process(self, parser):
        # parse args
        self.args = parser.parse_args()
        if self.args.timed:
            self.start_time = time.perf_counter()
        if self.args.recursive:
            files = self.args.dir.rglob('*.mkv')
        else:
            files = self.args.dir.glob('*.mkv')

        # process files
        with ThreadPoolExecutor() as executor:
            undefined_tracks = executor.map(self._check_track, files)

        # flatten list
        undefined_tracks = itertools.chain.from_iterable(undefined_tracks)

        # print report
        self._report(undefined_tracks)

    def _get_metadata(self, file):
        metadata = subprocess.run(['mkvmerge', '-J', str(file)], stdout=subprocess.PIPE)
        return json.loads(metadata.stdout)

    def _check_track(self, file):
        undefined_tracks = []
        metadata = self._get_metadata(file)

        for track in metadata['tracks']:
            if track['type'] in ['subtitles', 'audio'] and track['properties']['language'] == 'und':
                undefined_tracks.append({'file': file, 'track': track['properties']['number'], 'type': track['type']})

        return undefined_tracks

    def _report(self, results):
        # sort by filename
        results = list(results)
        results.sort(key=lambda entry: entry['file'])
        # create dictionary to sort out by track types
        types = {item['type']: [] for item in results}
        # actually sort the results into different lists
        for entry in results:
            types[entry['type']].append(entry)

        if len(types) == 0:
            print('No problems found.')
        else:
            for type, entries in types.items():
                print(f"The following files contained an undefined {type} track:")
                for entry in entries:
                    print(f"    {str(entry['file'].relative_to(self.args.dir))} (Track {entry['track']})")

        if self.args.timed:
            time_elapsed = pretty_time_delta(time.perf_counter()-self.start_time)
            print(f"Time elapsed: {time_elapsed}")


Operator = AuditOperator

