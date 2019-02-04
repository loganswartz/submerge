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
# Version: 0.5
# Last Modified: 2019/02/02
# ------------------------------------------------------------------------------------------------
# ----------------------------------
"""
aboutThisProgramShort = """
# ----------------------------------
# Submerge.py
# Version: 0.5
# ----------------------------------
"""

import argparse
import pathlib
import subprocess
import shutil
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re


# Wrapper for making paths from strings
def definePath(path: str):
    if path == None:
        return pathlib.Path.cwd()
    else:
        return pathlib.Path(path).resolve()


class messenger(object):

    def __init__(self, name: str):
        self.role = name

    def programInitMesg(self, verbose: bool = False):
        if verbose:
            print(aboutThisProgram)
        else:
            print(aboutThisProgramShort)

    def say(self, message: str):
        print(self.role + ": " + message)


class fileAuditor(object):
    def __init__(self, operation: str):
        self.role = operation
        self.errorCount = 0
        self.errorFiles = {}
        self.messenger = messenger(self.role)

    # Returns a plain list of objects in the dir matching a glob (defaults: CWD, *)
    def scanDirectory(self, globPattern: str = "*", searchDir: pathlib.Path = pathlib.Path.cwd(), recursive: bool = False, verbose: bool = False):
    
        if not recursive:
            #########################
            files = [file for file in searchDir.glob(globPattern) if file.is_file()]
            # This is equivalent to:
            #
            # files = []
            # for file in searchDir.glob(globPattern):
            #     if file.is_file():
            #         files.append(file)
            #
            # (list comprehensions are confusing, man) 
            #########################
        else:
            files = [file for file in searchDir.rglob(globPattern) if file.is_file()]
        # recursive vs nonrecursive globbing, default is nonrecursive

        if verbose == True:
            print("Found: ")
            for file in files:
                print(file)
        return files

    # Pass this an array of file extensions (ie [".txt", ".mkv", etc...]), and it finds all files in a dir with those extensions and packs them into a dictionary
    def findFiletype(self, desiredExts: list, directory: pathlib.Path = pathlib.Path.cwd(), recursive: bool = False, verbose: bool = False):
        files = {}
        
        for file in self.scanDirectory(searchDir=directory, recursive=recursive):
            if file.suffix in desiredExts:
                try:
                    files[file.suffix].append(file)
                except KeyError as error:
                    files[file.suffix] = []
                    files[file.suffix].append(file)
        #########################
        # above is a better implementation of the commented code below, the top only makes 1 pass through all files in the directory, the below makes n passes over all files, where n is the number of extensions you are looking forr
        #########################
        # for ext in desiredExts:
        #     files[ext] = self.scanDirectory(globPattern="*" + ext)
        #########################

        if verbose == True:
            print("Found: ")
            for filetype, filelist in files.items():
                print(filetype + " --> " + str(filelist))
        return files

    # extracts info from a given filename based on a selected regex, and returns it
    def regexExtraction(self, file: pathlib.Path, regexQuery: str, regexResultGroup: int = 0):
        regexList = {"seasonEpisode": r"[s|S]\d{1,3}\s?[e|E]\d{1,3}"}
        regex = re.compile(regexList.get(regexQuery))

        result = re.search(regex, file.name)
        if result:
            print("Extracted: " + result.group(regexResultGroup))
            return result.group(regexResultGroup)
        else:
            return ""

    def findSisterFile(self, file: pathlib.Path, validFileExts: list):
        # 1. find exact name match
        # 2. find SE match
        # 3. find fuzzy name match

        # get list of all files w/ valid filetype in the same directory (and child directories) as the input file
        fileList = self.findFiletype(validFileExts, file.parent, recursive=True)
        self.messenger.say("Searching for sister file to " + str(file) + "...")
        # ------------------ 1 ------------------ #
        for filetype, array in fileList.items():
            if file.with_suffix(filetype) in array:
                print("    Found ---> " + str(file.with_suffix(filetype)))
                return file.with_suffix(filetype)
        
        self.messenger.say("Perfect match not found, resorting to SE search...")

        # ------------------ 2 ------------------ #
        # extracts the season/episode from the filename
        se = self.regexExtraction(file, "seasonEpisode")
        if se == "":
            print("SE not found, skipping SE search.")
        else:
            for filetype, array in fileList.items():
                for item in array:
                    if self.regexExtraction(item, "seasonEpisode") == se:
                        print("    Found ---> " + str(file.with_suffix(filetype)))
                        return item
        self.messenger.say("SE match not found, resorting to best fuzzy match...")

        # ------------------ 3 ------------------ #
        bestMatch = [None, 0]
        for filetype, array in fileList.items():
            # hacky list comprehension to convert array of pathlib.Path objects to strings for compatability with fuzzywuzzy
            strArray = [str(file) for file in array]

            chosenFuzzyFile = process.extractOne(str(file.with_suffix(filetype)), strArray, scorer=fuzz.partial_ratio)
            if chosenFuzzyFile[1] > bestMatch[1]:
                bestMatch = chosenFuzzyFile

        if bestMatch[1] > 75:
            print("    Found (STR: " + str(bestMatch[1]) + ") ---> " + str(bestMatch[0])) 
            return definePath(bestMatch[0])

        print("No sister file found.")
        # No sister file found with the exact same name, or with the same SE as the file, or one with over 75% fuzzy name match confidence
        return None

    def recordFileError(self, errorFile: pathlib.Path, errorStatus: str, errorExtra: str = None, errorExtraMeta: str = None):
        self.errorFiles[errorFile.name] = {"file": errorFile, "error": errorStatus, "errorExtra": errorExtra, "errorExtraMeta": errorExtraMeta}
        print("Error on file " + errorFile.name + " was recorded.")

################################### copy or move?
    def moveFile(source: pathlib.Path, destination: pathlib.Path):
        try:
            shutil.copy2(str(source), str(destination))
        except (FileNotFoundError, shutil.Error) as error:
            self.recordFileError(errorFile=source, errorStatus=error, errorExtra=destination, errorExtraMeta="destination")
            print(error)
        except Exception as error:
            print("An unknown error occurred: " + error)

# __main__
# ------------------------------------------------------------------------------------------------
def main():
    cmdargparser = argparse.ArgumentParser()
    cmdargparser.add_argument("-m", "--mode", help="set the file manipulation mode", type=str, default="interactive")
    cmdargparser.add_argument("-v", "--viddir", help="specify the directory containing mkvs to operate on", type=str)
    cmdargparser.add_argument("-s", "--subdir", help="specify the directory containing subs to operate on", type=str)
    args = cmdargparser.parse_args()

    # allow for changing operation later
    programMode = args.mode
    viddir = definePath(args.viddir)
    subdir = definePath(args.subdir)
    fileOperator = fileAuditor("main")
    testMode = False

    validModes = ["submerge",
            "subtag",
            "organize",
            "rename",
            "interactive"]
    
    if programMode not in validModes:
        raise ValueError("Mode %r not found." % programMode)
    
    mainMessenger = messenger("main")
    mainMessenger.programInitMesg()
    mainMessenger.say("Program starting...\n")

    
    if programMode == "submerge":
        submerge(videoDir = viddir, subDir = subdir)

    if testMode == True:
        fileOperator.scanDirectory(verbose=True)
        fileOperator.findFiletype([".py", ".md", ".swp"], verbose=True)

    fileOperator.findSisterFile(file=definePath("/home/logans/Submerge/submerge.py"), validFileExts=[".sh"])
    exit(0)
    

# ------------------------------------------------------------------------------------------------


def submerge(videoDir: pathlib.Path = pathlib.Path.cwd(), subDir: pathlib.Path = None):
    if subDir is None:
        subDir = videoDir

    print("Mode selected: submerge\n")
    print("Looking for files...")

    fileOperation = fileAuditor("submerge")
    outDirectory = videoDir / "submerged"
    outDirectory.mkdir(exist_ok=True)

    videoFiles = fileOperation.scanDirectory(globPattern = "*.mkv", searchDir = videoDir, verbose=True)
    # subFiles = fileOperation.findFiletype(desiredExts = [".srt",".ass",".ssa",".usf",".pgs",".idx",".sub"], searchDir = subDir, verbose=True)
    
    for srcfile in videoFiles:
        subfile = fileOperation.findSisterFile(srcfile, [".srt",".ass",".ssa",".usf",".pgs",".idx"])
        outfile = outDirectory / srcfile.name
        if subfile.suffix == ".idx":
            # merge subfile into mkv and set language to English (.idx and .sub pairs)
            subprocess.run(["mkvmerge", "-o", outfile, srcfile, "--language", "0:eng", "--track-name", "0:English", "--default-track", "0:0", subfile, subfile.with_suffix(".sub")])
        else:
            # merge subfile into mkv and set language to English
            subprocess.run(["mkvmerge", "-o", outfile, srcfile, "--language", "0:eng", "--track-name", "0:English", "--default-track", "0:0", subfile])



if __name__ == "__main__":
    main()

