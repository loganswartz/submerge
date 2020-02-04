#!/usr/bin/env python3

# builtins
import pathlib
import subprocess


class AuditOperator(object):
    def __init__(self, subparser):
        pass

    def process(self, parser):
        args = parser.parse_args()
        files = [file for file in args.dir.glob('*.mkv')]

        for file in files:
            mkv_json = subprocess.run(['mkvmerge', 'J', str(file)], stdout=subprocess.PIPE)
            metadata = json.loads(mkv_json.stdout)

            for track in metadata:
                if track['type'] in ['subtitles', 'audio'] and track['properties']['language'] == 'und':
                    print(f"{file.stem} contains a {track['type']} track with an undefined language.")


Operator = AuditOperator
