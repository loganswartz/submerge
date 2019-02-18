#!/usr/bin/env python3

version = 0.8
modificationDate = "2019/02/07"
aboutThisProgram = f"""
# ----------------------------------
# ------------------------------------------------------------------------------------------------
# Submerge.py
# 
# A tool for batch-merging discrete subtitle files into their accompanying MKV video files
# (Python refactor of submerge.sh)
# 
# Written by: Logan Swartzendruber
# Version: {version}
# Last Modified: {modificationDate}
# ------------------------------------------------------------------------------------------------
# ----------------------------------
"""
aboutThisProgramShort = f"""
# ----------------------------------
# Submerge.py
# Version: {version}
# ----------------------------------
"""


import argparse
import pathlib
import subprocess
import shutil
import errno
import os
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
from classes import messenger
from classes import operation
import platform


# Wrapper for making paths from strings
def definePath(path: str):
    if path == None:
        return pathlib.Path.cwd()
    else:
        return pathlib.Path(path).resolve()

class SisterFileException(Exception):
    pass



# __main__
# ------------------------------------------------------------------------------------------------
def main():
    cmdargparser = argparse.ArgumentParser(description="A tool for batch-merging discrete subtitle files into their accompanying MKV video files, and other file manipulation.")
    cmdargparser.add_argument("-o", "--operation", help="set the file manipulation mode", type=str, default="interactive")
    cmdargparser.add_argument("-m", "--mediadir", help="specify the directory containing media files to operate on", type=pathlib.Path)
    cmdargparser.add_argument("-s", "--subdir", help="specify the directory containing subtitles to operate on", type=pathlib.Path)
    cmdargparser.add_argument("-v", "--verbose", help="turn on verbose output", action='store_true')
    args = cmdargparser.parse_args()

    # allow for changing operation later
    programMode = args.operation
    viddir = definePath(args.mediadir)
    subdir = definePath(args.subdir)
    fileOperator = operation.fileOperation("main")

    validModes = ["submerge",
            "subtag",
            "organize",
            "rename",
            "interactive"]
    
    if programMode not in validModes:
        raise ValueError(f"Mode {programMode} not found.")
    
    mainMessenger = messenger.messenger("main")
    mainMessenger.programInitMesg()
    mainMessenger.say("Program starting...\n")

    # check for mkvmerge executable
    if shutil.which("mkvmerge") == None:
        if platform.system() == "Windows":
            mkvmerge = pathlib.PureWindowsPath("C:/Program Files/MKVToolNix/mkvmerge.exe")
        elif platform.system() == "Linux" or platform.system() == "Darwin":
            mkvmerge = pathlib.PurePosixPath("/usr/bin/mkvmerge")
        # translates Pure path to regular path
        mkvmerge = pathlib.Path(mkvmerge).resolve()
    else:
        mkvmerge = definePath(shutil.which("mkvmerge"))
    if not mkvmerge.exists():
        mainMessenger.sayError("'mkvmerge' executable not found, operations utilizing mkvmerge will not be available.")
    
    if programMode == "submerge":
        submerge(videoDir = viddir, subDir = subdir)

#    print()
#    mainMessenger.say("Example of scanDirectory() on the CWD:")
#    fileOperator.scanDirectory(verbose=True)
#    print()
#    mainMessenger.say("Example of findFileType([\".py\", \".md\", \".swp\"]):")
#    fileOperator.findFiletype([".py", ".md", ".swp"], verbose=True)
#    print()
#    mainMessenger.say("Example of findSisterFile() looking for a sister or type \".sh\" to \"submerge.py\":")
#    fileOperator.findSisterFile(file=definePath("/home/logans/Submerge/submerge.py"), validFileExts=[".sh"])
    
    exit(0)
    

# ------------------------------------------------------------------------------------------------


def submerge(videoDir: pathlib.Path = pathlib.Path.cwd(), subDir = None):
    if subDir is None:
        subDir = videoDir

    print("Mode selected: submerge\n")
    print("Looking for files...")

    submergeOperation = operation.fileOperation("submerge")
    outDirectory = videoDir / "submerged"
    procDirectory = videoDir / "processed"
    outDirectory.mkdir(exist_ok=True)
    procDirectory.mkdir(exist_ok=True)

    videoFiles = submergeOperation.scanDirectory(globPattern = "*.mkv", directory = videoDir, verbose=True)
    subFiles = submergeOperation.findFiletype(desiredExts = [".srt",".ass",".ssa",".usf",".pgs",".idx",".sub"], directory = subDir, recursive=True, verbose=True)
    
    for srcfile in videoFiles:
        try:
            subfile = submergeOperation.findSisterFile(srcfile, fileList=subFiles)
        except FileNotFoundError as e:
            submergeOperation.recordFileError(errorFile=srcfile, errorStatus=e)
            submergeOperation.messenger.say("findSisterFile() for " + str(srcfile) + " skipped.\n")
            continue

        outfile = outDirectory / srcfile.name
        if subfile.suffix == ".idx":
            # merge subfile into mkv and set language to English (.idx and .sub pairs)
            subprocess.run(["mkvmerge", "-o", outfile, srcfile, "--language", "0:eng", "--track-name", "0:English", "--default-track", "0:0", subfile, subfile.with_suffix(".sub")])
        else:
            # merge subfile into mkv and set language to English
            subprocess.run(["mkvmerge", "-o", outfile, srcfile, "--language", "0:eng", "--track-name", "0:English", "--default-track", "0:0", subfile])
        print()
        submergeOperation.move(src, procDirectory, integrity_check=True)
    
    submergeOperation.generateReport(processedDirectory=procDirectory, outputDirectory=outDirectory)
    # submerge operation done


if __name__ == "__main__":
    main()

