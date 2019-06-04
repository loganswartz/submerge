#!/usr/bin/env python3

"""
Miscellaneous functions that aren't big / important enough to be contained in t
heir own file.
"""

# builtin modules
from pathlib import Path
import subprocess
import json
import string
import random

# Wrapper for making paths from strings
def definePath(path: str):
    if path == None:
        return Path.cwd()
    else:
        return Path(path).expanduser().resolve()

class SisterFileException(Exception):
    pass

def get_sequences(inList: list):
    segments = []
    temp = []
    for i,strIndex in enumerate(inList):
        if i == 0:
            temp.append(strIndex)
        elif i == len(inList)-1:
            temp.append(strIndex)
            segments.append(temp)
            continue
        if inList[i+1] != strIndex+1:
            temp.append(strIndex)
            segments.append(temp)
            temp = []
            temp.append(inList[i+1])
    return segments

def get_media_json(src: Path):
    mkvmergeOutput = subprocess.run(["mkvmerge", "-J", src],
                         stdout=subprocess.PIPE)
    return json.loads(mkvmergeOutput.stdout)

def gen_rand_string(length: int = 40, chars = string.ascii_lowercase +
                    string.digits):
    return ''.join(random.choice(chars) for x in range(length))
