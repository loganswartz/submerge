#!/usr/bin/env python3

# Imports {{{
# builtins
from collections import defaultdict
import json
import itertools
import pathlib
import shlex
import subprocess
from typing import (
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Tuple,
    TypeVar,
    Union,
    overload,
)

# 3rd party
import pycountry

# }}}


def pretty_time_delta(seconds):
    _seconds = int(seconds)
    days, _seconds = divmod(_seconds, 24 * 60 ** 2)
    hours, _seconds = divmod(_seconds, 60 ** 2)
    minutes, _seconds = divmod(_seconds, 60)
    seconds = seconds - float(
        (days * 24 * 60 ** 2) + (hours * 60 ** 2) + (minutes * 60)
    )
    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds:.0f}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds:.0f}s"
    elif minutes > 0:
        return f"{minutes}m {seconds:.1f}s"
    else:
        return f"{seconds:.2f}s"


def get_docstring(obj):
    try:
        lines = [line.strip() for line in obj.__doc__.split("\n") if line.strip()]
        return lines[0]
    except AttributeError:
        return None


def AbsolutePath(path):
    return pathlib.Path(path).expanduser().resolve()


def get_metadata(file: pathlib.Path):
    cmd = ["mkvmerge", "-J", str(file)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    metadata = json.loads(proc.stdout)
    return metadata


def get_files(
    paths: Iterable[pathlib.Path], recurse: bool = False, glob: str = "*.mkv"
):
    """
    Apply a glob to all specified paths, and collate + dedupe the results.
    """
    results = partition(paths, lambda path: path.is_dir())
    dirs, files = results[True], results[False]

    for folder in dirs:
        contents = folder.rglob(glob) if recurse else folder.glob(glob)
        files = itertools.chain(files, contents)

    # filter and dedupe
    return list({file for file in files if file.is_file()})


def get_track_pattern(metadata):
    pattern = []
    for track in metadata["tracks"]:
        try:
            pattern.append((track["properties"]["number"], track["type"][0]))
        except KeyError:
            continue
    return pattern


def language(string):
    try:
        if len(string) == 2:
            lang = pycountry.languages.get(alpha_2=string)
        elif len(string) == 3:
            lang = pycountry.languages.get(alpha_3=string)
        else:
            lang = pycountry.languages.lookup(string)
        return lang
    except LookupError:
        raise ValueError from None


Item = TypeVar("Item")
Sentinel = TypeVar("Sentinel")


@overload
def partition(
    iterable: Iterable[Item],
    key: Callable[[Item], Sentinel],
    indexed: Literal[False] = False,
) -> Dict[Sentinel, List[Item]]:
    ...


@overload
def partition(
    iterable: Iterable[Item], key: Callable[[Item], Sentinel], indexed: Literal[True]
) -> Dict[Sentinel, List[Tuple[int, Item]]]:
    ...


@overload
def partition(
    iterable: Iterable[Item], key: Callable[[Item], Sentinel], indexed: bool
) -> Union[Dict[Sentinel, List[Item]], Dict[Sentinel, List[Tuple[int, Item]]]]:
    ...


def partition(
    iterable: Iterable[Item], key: Callable[[Item], Sentinel], indexed: bool = False
) -> Union[Dict[Sentinel, List[Item]], Dict[Sentinel, List[Tuple[int, Item]]]]:
    """
    Partition an iterable into parts based on a key function.
    Similar to itertools.groupby() or the Unix `uniq` tool, after a sort.
    """
    results = defaultdict(list)
    # add the index of the item to the results if indexed is true
    iterator = enumerate(iterable) if indexed else iterable
    for item in iterator:
        sentinel = key(item[1] if indexed else item)
        results[sentinel].append(item)

    return results


def quote_cmd(cmd: List):
    return " ".join(shlex.quote(str(token)) for token in cmd)
