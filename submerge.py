#!/usr/bin/env python

aboutThisProgram = """
# ----------------------------------
# ------------------------------------------------------------------------------------------------
# Submerge.py
# 
# A tool for batch-merging discrete subtitle files into their accompanying MKV video files
# (Python refactor of submerge.sh)
# 
# Written by: Logan Swartzendruber
# Version: 0.1
# Last Modified: 2019/1/29
# ------------------------------------------------------------------------------------------------
# ----------------------------------

"""

import argparse
import pathlib
import subprocess


# Wrapper for making paths from strings
def definePath(path: str):
    return pathlib.Path(path)


# Returns a plain list of objects in the dir matching a glob (defaults: CWD, *)
def scanDirectory(globPattern: str = "*", searchDir: pathlib.Path = pathlib.Path.cwd(), verbose: bool = False):

    #########################
    files = [file for file in searchDir.glob(globPattern)]
    # This is equivalent to:
    #
    # files = []
    # for file in searchDir.glob(globPattern):
    #     files.append(file)
    #
    # (list comprehensions are confusing, man) 
    #########################
    if verbose == True:
        print("Found: ")
        for file in files:
            print(file)
    return files


# Pass this an array of file extensions (ie [".txt", ".mkv", etc...]), and it finds all files in a dir with those extensions and packs them into a dictionary
def findExtInDir(desiredExts: list, directory: pathlib.Path = pathlib.Path.cwd(), verbose: bool = False):
    files = {}
    for ext in desiredExts:
        files[ext] = scanDirectory(globPattern="*" + ext)
    if verbose == True:
        print("Found: ")
        for filetype, filelist in files.items():
            print(filetype + " --> " + str(filelist))
    return files


class messenger(object):

    def __init__(self, name: str):
        self.role = name

    def programInit(self):
        print(aboutThisProgram)


# __main__
# ------------------------------------------------------------------------------------------------
def main():
    cmdargparser = argparse.ArgumentParser()
    cmdargparser.add_argument("-m", "--mode", help="set the file manipulation mode", type=str, default="interactive")
    cmdargparser.add_argument("-v", "--viddir", help="specify the directory containing mkvs to operate on", type=str)
    cmdargparser.add_argument("-s", "--subdir", help="specify the directory containing subs to operate on", type=str)
    args = cmdargparser.parse_args()
    
    programModes = ["submerge",
            "subtag",
            "organize",
            "rename",
            "interactive"]
    
    if args.mode not in programModes:
        raise ValueError("Mode %r not found." % args.mode)
    
    mainMessenger = messenger("mainThread")
    mainMessenger.programInit()
    scanDirectory(verbose=True)
    print(findExtInDir([".py", ".md", ".swp"], verbose=True))
    

# ------------------------------------------------------------------------------------------------


def submerge(videoDir: pathlib.Path, subDir: pathlib.Path = None):
    if subDir is None:
        subDir = videoDir
    print("test")



if __name__ == "__main__":
    main()

