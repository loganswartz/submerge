#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor
import time
import itertools

from submerge.utils import pretty_time_delta, get_metadata


class AuditOperator(object):
    """
    Scan a directory and audit all the files in it, noting any issues that could be fixed.
    """
    def __init__(self, subparser):
        subparser.add_argument('-t', '--timed', help='Report the time taken to audit', action='store_true')
        subparser.add_argument('-p', '--pattern', help='Produce a pattern that can be used with the \'tracks\' module', action='store_true')

    def process(self, parser):
        # parse args
        self.args = parser.parse_args()
        if self.args.timed:
            self.start_time = time.perf_counter()
        if self.args.path.is_file():
            files = [self.args.path]
        elif self.args.recursive:
            files = list(self.args.path.rglob('*.mkv'))
        else:
            files = list(self.args.path.glob('*.mkv'))

        if not files:
            print('No files found.')
            return

        # decide the operation to carry out
        if self.args.pattern:
            func = self._pattern
        else:
            func = self._check_track

        # process files
        with ThreadPoolExecutor() as executor:
            results = executor.map(func, files)

        if self.args.pattern:
            for result in results:
                print(f"{result[1]} - {result[0].relative_to(self.args.path)}")
        else:
            # flatten list
            undefined_tracks = itertools.chain.from_iterable(results)

            # print report
            self._report(undefined_tracks)

    def _pattern(self, file):
        try:
            metadata = get_metadata(file)
        except KeyError:
            print(f'ERROR: {file} could not be read.')
            return

        pattern = []
        for track in metadata['tracks']:
            try:
                pattern.append(str(track['properties']['number']) + track['type'][0])
            except KeyError:
                continue
        pattern.sort(key=lambda track: track[0])
        return (file, ':'.join(pattern))

    def _check_track(self, file):
        undefined_tracks = []
        metadata = get_metadata(file)

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
                    if self.args.path.is_file():
                        name = str(entry['file'])
                    else:
                        name = str(entry['file'].relative_to(self.args.path))
                    print(f"    (Track {entry['track']}) {name}")

        if self.args.timed:
            time_elapsed = pretty_time_delta(time.perf_counter() - self.start_time)
            print(f"Time elapsed: {time_elapsed}")


Operator = AuditOperator

