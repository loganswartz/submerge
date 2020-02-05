#!/usr/bin/env python3

import pathlib
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor
import time
from submerge.utils import pretty_time_delta


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
        undefined_tracks = {'subtitles': [], 'audio': []}
        with ThreadPoolExecutor() as executor:
            work = executor.map(self._check_tracks, files)
            # every call to self._check_tracks returns an dictionary like undefined_tracks, here we merge them all together
            for file in work:
                for type in undefined_tracks:
                    undefined_tracks[type].extend(file[type])

        # print report
        self._report(undefined_tracks)

    def _get_metadata(self, file):
        metadata = subprocess.run(['mkvmerge', '-J', str(file)], stdout=subprocess.PIPE)
        return json.loads(metadata.stdout)

    def _check_tracks(self, file):
        undefined_tracks = {'subtitles': [], 'audio': []}
        metadata = self._get_metadata(file)

        for track in metadata['tracks']:
            if track['type'] in ['subtitles', 'audio'] and track['properties']['language'] == 'und':
                undefined_tracks[track['type']].append(file)

        return undefined_tracks

    def _report(self, results):
        for type in results:
            results[type].sort()
            if results[type]:
                print(f"The following files contained an undefined {type} track:")
                for file in results[type]:
                    print(f"    {str(file.relative_to(self.args.dir))}")
            else:
                print('No problems found.')
        if self.args.timed:
            time_elapsed = pretty_time_delta(time.perf_counter()-self.start_time)
            print(f"Time elapsed: {time_elapsed}")


Operator = AuditOperator
