#!/usr/bin/env python3

# builtins
import pathlib
import subprocess
import json


class AuditOperator(object):
    """
    Scan a directory and audit all the files in it, noting any issues that
    could be fixed.
    """
    def __init__(self, subparser):
        subparser.add_argument('-r', '--recursive', help='Recurse into directories', action='store_true')

    def process(self, parser):
        args = parser.parse_args()
        if args.recursive:
            files = [file for file in args.dir.rglob('*.mkv')]
        else:
            files = [file for file in args.dir.glob('*.mkv')]

        undefined_tracks = {'subtitles': [], 'audio': []}
        for file in files:
            mkv_json = subprocess.run(['mkvmerge', '-J', str(file)], stdout=subprocess.PIPE)
            metadata = json.loads(mkv_json.stdout)

            for track in metadata['tracks']:
                if track['type'] in ['subtitles', 'audio'] and track['properties']['language'] == 'und':
                    undefined_tracks[track['type']].append(file)

        for type in undefined_tracks:
            undefined_tracks[type].sort()
            if undefined_tracks[type]:
                print(f"The following files contained an undefined {type} track:")
                for file in undefined_tracks[type]:
                    print(f"    {str(file.relative_to(args.dir))}")
            else:
                print('No problems found.')


Operator = AuditOperator
