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


    # main args
    cmdparse = argparse.ArgumentParser(
            description=("A tool for batch-merging discrete subtitle files "
            "into their accompanying MKV video files, and other file "
            "manipulation."), conflict_handler="resolve")
    cmdparse.add_argument("-v",
                          "--verbose",
                          help="turn on verbose output",
                          action="store_true")
    subparse = cmdparse.add_subparsers(help="operation types",dest="operation")

    # merge args
    mergeparse = subparse.add_parser("merge",
                                     help="Merge subtitle files and mkv files")
    mergeparse.add_argument("-m", "--media", type=lambda p: definePath(p),
                            help=("Path to the directory containing media "
                                  "files to operate on"))
    mergeparse.add_argument("-s", "--subs", type=str, help=("Path to the "
                            "directory containing subtitle files to operate "
                            "on"))
    # tag args
    tagparse = subparse.add_parser("tag",
                                   help=("Identity and label untagged tracks "
                                   "in media files"))
    tagparse.add_argument("-m", "--media", type=lambda p: definePath(p),
                          help=("Path to the directory containing media files "
                                "to operate on"))
    tagparse.add_argument("-l", "--lang", type=str, help=("Tag override "
                          "language"))

    # mod args
    modparse = subparse.add_parser("mod",
                                   help="Modify track tags on media files")
    modparse.add_argument("-m", "--media", type=lambda p: definePath(p),
                          help=("Path to the directory containing media files "
                                "to operate on"))

    # other args
    auditparse = subparse.add_parser("audit",
                                   help="Analyze and audit media files")
    auditparse.add_argument("-m", "--media", type=lambda p: definePath(p),
                          help=("Path to the directory containing media files "
                                "to operate on"))

    organizeparse = subparse.add_parser("organize",
                                   help="Organize media files")
    organizeparse.add_argument("-m", "--media", type=lambda p: definePath(p),
                               help=("Path to the directory containing media "
                                     "files to operate on"))

    interactiveparse = subparse.add_parser("interactive",
                                   help="Interactive prompt")
    interactiveparse.add_argument("-m", "--media",type=lambda p: definePath(p),
                                  help=("Path to the directory containing "
                                        "media files to operate on"))


    args = cmdparse.parse_args()

    # allow for changing operation later
    fileOperator = fileManipulator("main")

    mainMessenger = messenger.messenger("main")
    if args.verbose:
        mainMessenger.programInitMesg(doc=__doc__,
                                      author=__author__,
                                      version=__version__,
                                      verbose=True)
        mainMessenger.say("Program starting...\n")

    # check for mkvmerge executable
    if shutil.which("mkvmerge") != None:
        mkvmerge = definePath(shutil.which("mkvmerge"))
    else:
        if platform.system() == "Windows":
            mkvmerge = pathlib.PureWindowsPath(("C:/Program Files/MKVToolNix/"
                                                "mkvmerge.exe"))
        elif platform.system() == "Linux" or platform.system() == "Darwin":
            mkvmerge = pathlib.PurePosixPath("/usr/bin/mkvmerge")
        # translates Pure path to regular path
        mkvmerge = pathlib.Path(mkvmerge).resolve()
    if not mkvmerge.exists():
        mainMessenger.sayError(("'mkvmerge' executable not found, operations "
                                "utilizing mkvmerge will not be available."))

    operations = ["merge",
                  "tag",
                  "mod",
                  "audit",
                  "organize",
                  "interactive"]

    # validate and launch selected operation
    if args.operation not in operations:
        raise ValueError(f"Mode {args.operation} not found.")
    elif args.operation == "merge":
        merge(vidsrc = viddir, subsrc = subdir)
    elif args.operation == "tag":
        tag(vidsrc = viddir)
    elif args.operation == "audit":
        audit(vidsrc = viddir, subsrc = subdir)
    elif args.operation == "interactive":
        print(args.media)

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

