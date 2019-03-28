#!/usr/bin/env python3

"""Submerge.py: A tool for batch-merging discrete subtitle files into their
accompanying MKV video files.
"""

__version__ = "0.9"

__author__ = "Logan Swartzendruber"
__status__ = "Development"

"""
Class objects are CapitalizedWords
Functions are snake_case
Simple variables are CapWords
"""

# builtin modules
import argparse
import pathlib
import subprocess
import shutil
import errno
import os

# 3rd party modules

# my modules
from submerge.objects import messenger
from submerge.objects.fileManipulator import fileManipulator
from submerge.utils import definePath
from submerge.operations import merge, tag, mod, audit



def main():
    """
    Main loop of the program that configures and runs the desired operation.
    """


    cmdparse = argparse.ArgumentParser(
            description=("A tool for batch-merging discrete subtitle files "
            "into their accompanying MKV video files, and other file "
            "manipulation."))


    cmdparse.add_argument("-o",
                          "--operation",
                          help="set the file manipulation mode",
                          type=str,
                          default="interactive")
    cmdparse.add_argument("-m",
                          "--mediadir",
                          help=("specify the directory containing media "
                          "files to operate on"),
                          type=pathlib.Path)
    cmdparse.add_argument("-s", 
                          "--subdir",
                          help=("specify the directory containing "
                          "subtitles to operate on"),
                          type=pathlib.Path)
    cmdparse.add_argument("-v",
                          "--verbose",
                          help="turn on verbose output",
                          action='store_true')
    
    args = cmdparse.parse_args()

    # allow for changing operation later
    programMode = args.operation
    viddir = definePath(args.mediadir)
    subdir = definePath(args.subdir)
    fileOperator = fileManipulator("main")

    validModes = ["merge",
                  "tag",
                  "mod",
                  "audit",
                  "organize",
                  "rename",
                  "interactive"]
    
    mainMessenger = messenger.messenger("main")
    mainMessenger.programInitMesg(doc=__doc__,
                                  author=__author__,
                                  version=__version__,
                                  verbose=True)
    mainMessenger.say("Program starting...\n")

    # check for mkvmerge executable
    if shutil.which("mkvmerge") == None:
        if platform.system() == "Windows":
            mkvmerge = pathlib.PureWindowsPath(("C:/Program Files/MKVToolNix/"
                                                "mkvmerge.exe"))
        elif platform.system() == "Linux" or platform.system() == "Darwin":
            mkvmerge = pathlib.PurePosixPath("/usr/bin/mkvmerge")
        # translates Pure path to regular path
        mkvmerge = pathlib.Path(mkvmerge).resolve()
    else:
        mkvmerge = definePath(shutil.which("mkvmerge"))
    if not mkvmerge.exists():
        mainMessenger.sayError(("'mkvmerge' executable not found, operations "
                                "utilizing mkvmerge will not be available."))
    # validate and launch selected operation
    if programMode not in validModes:
        raise ValueError(f"Mode {programMode} not found.")
    elif programMode == "merge":
        merge(vidsrc = viddir, subsrc = subdir)
    elif programMode == "tag":
        tag(vidsrc = viddir)
    elif programMode == "audit":
        audit(vidsrc = viddir, subsrc = subdir)

    print()
    mainMessenger.say("Example of scanDirectory() on the CWD:")
    fileOperator.scanDirectory(verbose=True)
"""
    print()
    mainMessenger.say("Example of findFileType([\".py\", \".md\", \".swp\"]):")
    fileOperator.findFiletype([".py", ".md", ".swp"], verbose=True)
    print()
    
    mainMessenger.say(("Example of findSisterFile() looking for a sister or "
                       "type \".sh\" to \"merge.py\":"))
    fileOperator.findSisterFile(
                        file=definePath("/home/logans/Submerge/merge.py"),
                        validFileExts=[".sh"])
""" 
    

# ----------------------------------------------------------------------------

if __name__ == "__main__":
    main()

