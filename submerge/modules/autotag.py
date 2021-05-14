#!/usr/bin/env python3

# Imports {{{
# builtins
import json
import logging
import pathlib
import subprocess
from tempfile import NamedTemporaryFile
from typing import Iterable

# 3rd party
from langdetect import detect
import click

# local modules
from submerge.modules.base import path_args
from submerge.utils import get_files, language

# }}}


log = logging.getLogger(__name__)


@click.command()
@path_args
@click.option(
    "-c", "--confirm", help="Ask for confirmation before processing", is_flag=True
)
def autotag(paths: Iterable[pathlib.Path], recursive: bool, confirm: bool):
    """
    Auto guess-and-tag the language of undefined subtitle tracks.
    """

    files = get_files(paths, recurse=recursive)

    jobs = []
    for file in files:
        proc = subprocess.run(["mkvmerge", "-J", file], stdout=subprocess.PIPE)
        metadata = json.loads(proc.stdout)

        undefined = (
            track["id"]
            for track in metadata["tracks"]
            if track["type"] == "subtitles" and track["properties"]["language"] == "und"
        )
        modifications = []
        for track in undefined:
            track_data = NamedTemporaryFile()
            subprocess.run(
                [
                    "mkvextract",
                    file,
                    "tracks",
                    f"track:{track}",
                    "{track}:{track_data.name}",
                ]
            )
            lang = language(detect(track_data.read()))
            modifications.append((track, lang))
        jobs.append((file, modifications))

        confirmed = False
        if confirm:
            log.info("The following changes will be made:")
            for file, modifications in jobs:
                log.info(f"{file}:")
                for track, lang in modifications:
                    log.info(f'    Track {track}: "und" --> "{lang.alpha3}"')
            confirmed = input("Would you like to make these changes? [y/n] ")

        if (not confirm) or confirmed:
            # actually tag the files
            for file, modifications in jobs:
                for track, lang in modifications:
                    set_track_lang(file, track, lang)


def set_track_lang(file, track, lang):
    proc = subprocess.run(
        [
            "mkvpropedit",
            file,
            "--edit",
            f"track:{track}",
            "--set",
            f"language={lang.alpha3}",
        ]
    )
    return not proc.returncode  # True if returned 0, otherwise False
