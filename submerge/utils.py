#!/usr/bin/env python3

# builtins
import pathlib
import subprocess
import json
import itertools


def pretty_time_delta(seconds):
    _seconds = int(seconds)
    days, _seconds = divmod(_seconds, 86400)
    hours, _seconds = divmod(_seconds, 3600)
    minutes, _seconds = divmod(_seconds, 60)
    seconds = seconds - float((days * 86400) + (hours * 3600) + (minutes * 60))
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
        lines = [line.strip() for line in obj.__doc__.split('\n') if line.strip()]
        return lines[0]
    except AttributeError:
        return None


def AbsolutePath(path):
    return pathlib.Path(path).expanduser().resolve()


def get_metadata(file: pathlib.Path):
    proc = subprocess.run(['mkvmerge', '-J', str(file)], stdout=subprocess.PIPE)
    metadata = json.loads(proc.stdout)
    return metadata


def get_files(path, recursive = False, filetypes: list = ['.mkv']):
    path = AbsolutePath(path)
    if path.is_file() and path.suffix in filetypes:
        files = [path]
    else:
        files = ()
        for type in filetypes:
            if recursive:
                files = itertools.chain(files, path.rglob('*' + type))
            else:
                files = itertools.chain(files, path.glob('*' + type))
    return files


def get_track_pattern(metadata):
    pattern = []
    for track in metadata['tracks']:
        try:
            pattern.append((track['properties']['number'], track['type'][0]))
        except KeyError:
            continue
    return pattern


class InvertableDict(dict):
    def inverted(self):
        values = {val for arr in self.values() for val in arr}
        new = InvertableDict({value: [] for value in values})
        for key, values in self.items():
            for value in values:
                new[value].append(key)
        return new

def language(string):
    try:
        lang = pycountry.languages.lookup(string)
        return lang
    except LookupError:
        raise ValueError from None

