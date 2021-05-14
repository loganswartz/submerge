#!/usr/bin/env python3

# Imports {{{
# builtins
import logging
import pathlib
from typing import NamedTuple, Tuple

# 3rd party
import click

# local modules
from submerge.modules.base import path_args
from submerge.utils import get_files, language, quote_cmd

# }}}


log = logging.getLogger(__name__)


@click.command()
@path_args
@click.option(
    "-s",
    "--subtitle",
    "subtitles",
    help="Subtitle file and its language",
    metavar="FILE LANG",
    type=(click.Path(exists=True, dir_okay=False, path_type=pathlib.Path), language),
    nargs=2,
    multiple=True,
)
def merge(paths, recursive, subtitles):
    """
    Merge subtitles into their matching video files.
    """
    files = get_files(paths, recurse=recursive)

    filetypes = [".srt", ".ass", ".ssa", ".usf", ".pgs", ".idx", ".sub"]
    if not all(file.suffix in filetypes for file, _ in subtitles):
        raise ValueError("A passed subtitle file has an unsupported extension")

    cmds = [merge_command(file, *subtitles) for file in files]

    log.info('\n'.join(quote_cmd(cmd) for cmd in cmds))


class Language(NamedTuple):
    alpha_2: str
    alpha_3: str
    name: str
    scope: str
    type: str


def merge_command(file, *subtitles: Tuple[pathlib.Path, Language]):
    def track_args(file: pathlib.Path, lang: Language):
        args = [
            "--default-track",
            "0:0",
            "--language",
            f"0:{lang.alpha_3}",
            "--track-name",
            f"0:{lang.name}",
            file,
        ]
        if file.suffix == ".idx":
            args.append(file.with_suffix(".sub"))

        return args if file.suffix != ".sub" else None

    cmd = [
        "mkvmerge",
        "-o",
        file.with_name(file.stem + '-merged' + file.suffix),
        file,
    ]

    for subtitle in subtitles:
        file, lang = subtitle
        args = track_args(file, lang)
        if args is not None:
            cmd.extend(args)

    return cmd
