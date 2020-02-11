#!/usr/bin/env python3

# builtins
import pathlib
from math import floor


def pretty_time_delta(seconds):
    _seconds = int(seconds)
    days, _seconds = divmod(_seconds, 86400)
    hours, _seconds = divmod(_seconds, 3600)
    minutes, _seconds = divmod(_seconds, 60)
    seconds = seconds - float((days*86400)+(hours*3600)+(minutes*60))
    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds:.0f}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds:.0f}s"
    elif minutes > 0:
        return f"{minutes}m {seconds:.1f}s"
    else:
        return f"{seconds:.2f}s"


def get_docstring(obj):
    if obj.__doc__:
        lines = [line.strip() for line in obj.__doc__.split('\n') if line.strip()]
        return lines[0]
    else:
        return None

