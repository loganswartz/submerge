#!/usr/bin/env python3

# builtins
import subprocess
from tempfile import NamedTemporaryFile
import json

# 3rd party
import pycountry
from langdetect import detect

# this module
from submerge.utils import language


class AutotagOperator(object):
    def __init__(self, subparser):
        subparser.add_argument('-c', '--confirm', help='Ask for confirmation before processing', action='store_true')

    def process(self, parser):
        args = parser.parse_args()
        self.args = args
        if args.path.is_file() and args.path.suffix == '.mkv':
            files = [args.path]
        elif args.recursive:
            files = args.path.rglob('*.mkv')
        else:
            files = args.path.glob('*.mkv')

        jobs = []
        for file in files:
            proc = subprocess.run(["mkvmerge", "-J", file], stdout=subprocess.PIPE)
            metadata = json.loads(proc.stdout)

            undefined = (track["id"] for track in metadata["tracks"]
                         if track["type"] == "subtitles" and
                         track["properties"]["language"] == "und")
            modifications = []
            for track in undefined:
                track_data = NamedTemporaryFile()
                subprocess.run(["mkvextract", file, "tracks", f"track:{track}",
                                "{track}:{track_data.name}"])
                lang = language(detect(track_data.read()))
                modifications.append((track, lang))
            jobs.append((file, modifications))

            confirmed = False
            if args.confirm:
                print("The following changes will be made:")
                for file, modifications in jobs:
                    print(f"{file}:")
                    for track, lang in modifications:
                        print(f"    Track {track}: \"und\" --> \"{lang.alpha3}\"")
                confirmed = input("Would you like to make these changes? [y/n] ")

            if (args.confirm and confirmed) or (not args.confirm):
                # actually tag the files
                for file, modifications in jobs:
                    for track, lang in modifications:
                        set_track_lang(file, track, lang)


def set_track_lang(file, track, lang):
    proc = subprocess.run(["mkvpropedit", file, "--edit", f"track:{track}",
                           "--set", f"language={lang.alpha3}"])
    return not proc.returncode   # True if returned 0, otherwise False


Operator = AutotagOperator

