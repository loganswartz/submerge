#!/usr/bin/env python3

# builtin modules
import subprocess

# my modules
from submerge.utils import definePath

class mkvCommand(object):

    def __init__(self, program: pathlib.Path, file):
        self.program = program
        self.file = definePath(file)
        self.full_command = []
        self.full_command.append(self.program)
        self.full_command.append(self.file)

    def run(self):
        return subprocess.run(self.full_command, stdout=subprocess.PIPE)

class propeditCommand(mkvCommand):

    def __init__(self, program: pathlib.Path, file):
        super(mkvCommand, self).__init__(program, file)

    def set_track_lang(self, track: int, language: str):
        self.full_command.append("--edit")
        self.full_command.append(f"track:{track+1}")
        self.full_command.append("--set")
        self.full_command.append(f"language={language}")

    def run(self):
        return super(mkvCommand, self).run()

class extractCommand(mkvCommand):

    def __init__(self, program: pathlib.Path, file):
        super(mkvCommand, self).__init__(program, file)

    def add_track(self, track: str, filepath):
        self.full_command.append("tracks")
        self.full_command.append(track+"."+filepath)

    def run(self):
        return super(mkvCommand, self).run()

