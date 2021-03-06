#!/usr/bin/env python3

# builtins
from concurrent.futures import ThreadPoolExecutor
import subprocess

# 3rd party
import pycountry

# this module
from submerge.utils import language

# monkeypatch to handle langdetect returning nonstandard identifiers
# pycountry.languages.lookup('cmn').alpha_2 = 'zh-cn'
# pycountry.languages.lookup('yue').alpha_2 = 'zh-tw'


class TagOperator(object):
    def __init__(self, subparser):
        subparser.add_argument('-l', '--language', help='Language the track will be set to', type=language, required=True)
        subparser.add_argument('-t', '--track', help='Track to modify', type=int, required=True)
        subparser.add_argument('-s', '--simulate', help='Print out the command to be executed instead of actually executing it', action='store_true')
        # TODO
        # subparser.add_argument('-u', '--only-undefined', help='Only modify tracks when they are undefined', action='store_true')
        # subparser.add_argument('-c', '--confirm', help='Ask for confirmation before processing', action='store_true')

    def process(self, parser):
        args = parser.parse_args()
        self.args = args
        if args.path.is_file() and args.path.suffix == '.mkv':
            files = [args.path]
        elif args.recursive:
            files = args.path.rglob('*.mkv')
        else:
            files = args.path.glob('*.mkv')

        with ThreadPoolExecutor() as executor:
            results = executor.map(lambda file: self._edit_track(file, args.track, language=args.language), files)

        if args.verbose:
            print('Command outputs:')
            for output in results:
                print(output.stdout.decode('utf-8'))

        if not args.simulate:
            print('All files modified.')

    def _edit_track(self, file, track, **kwargs):
        cmd = ['mkvpropedit', str(file.expanduser().resolve()), '--edit', f'track:@{track}']
        for key, value in kwargs.items():
            cmd.extend(['--set', f'{key}={value.alpha_3}'])

        if self.args.simulate:
            print(cmd)
            return cmd
        else:
            propedit = subprocess.run(cmd, stdout=subprocess.PIPE)
            return propedit


Operator = TagOperator

