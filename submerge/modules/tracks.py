#!/usr/bin/env python3

# builtins
import pathlib
from enum import Enum
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor


class TracksOperator(object):
    def __init__(self, subparser):
        subparser.add_argument('-o', '--old-order', help='The current track ordering')
        subparser.add_argument('-n', '--new-order', help='The new desired track ordering')
        subparser.add_argument('-p', '--pattern', help='Only modify a file if it matches the specified track pattern')
        subparser.add_argument('-r', '--recursive', help='Recurse into directories', action='store_true')

    def process(self, parser):
        self.args = parser.parse_args()
        if self.args.path.is_file():
            files = [self.args.path]
        elif self.args.recursive:
            files = list(self.args.path.rglob('*.mkv'))
        else:
            files = list(self.args.path.glob('*.mkv'))

        if not files:
            print('No files found.')
            return

        results = {'pass': [], 'fail': []}
        for file in files:
            if not self.args.pattern or (self.args.pattern and self._test(file)):
                results['pass'].append(file)
            else:
                results['fail'].append(file)

        results['pass'].sort()
        results['fail'].sort()

        if self.args.pattern:
            print('The following files matched the pattern:')
            for file in results['pass']:
                print(f"    {file.relative_to(self.args.path)}")
            print('The following files did not match the pattern:')
            for file in results['fail']:
                print(f"    {file.relative_to(self.args.path)}")

        # process files
        with ThreadPoolExecutor() as executor:
            processed = executor.map(self._modify_track, results['pass'])

        return processed

    def _modify_track(self, file):
        cmd = ['mkvpropedit', str(file)]
        for old, new in zip(self.args.old_order.split(':'), self.args.new_order.split(':')):
            cmd += ['--edit', f"track:{old}", '--set', f"track-number={new}"]
        # print(' '.join(cmd))

        proc = subprocess.run(cmd, stdout=subprocess.PIPE)
        return proc

    def _test(self, file):
        class TrackType(Enum):
            video = 'v'
            audio = 'a'
            subtitles = 's'

        user_pairings = {int(pair[0]): TrackType(pair[1]) for pair in self.args.pattern.split(':')}

        try:
            proc = subprocess.run(['mkvmerge', '-J', str(file)], stdout=subprocess.PIPE)
            metadata = json.loads(proc.stdout)
            real_pairings = {int(track['properties']['number']): TrackType[track['type']] for track in metadata['tracks']}
        except KeyError:
            print(f'ERROR: {file} failed to be read.')
            return False

        # check if user_pairings is a subset of real_pairings
        return user_pairings.items() <= real_pairings.items()

Operator = TracksOperator

