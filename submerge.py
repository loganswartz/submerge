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
import shutil


# Wrapper for making paths from strings
def definePath(path: str):
    if path == None:
        return pathlib.Path.cwd()
    else:
        return pathlib.Path(path).resolve()


class messenger(object):

    def __init__(self, name: str):
        self.role = name

    def programInit(self):
        print(aboutThisProgram)

    def say(self, message: str):
        print(self.role + ": " + message)


class fileAuditor(object):
    def __init__(self, operation: str):
        self.role = operation
        self.errorCount = 0
        self.errorFiles = {}
        self.messenger = messenger(self.role)

    # Returns a plain list of objects in the dir matching a glob (defaults: CWD, *)
    def scanDirectory(self, globType: str = "glob" , globPattern: str = "*", searchDir: pathlib.Path = pathlib.Path.cwd(), verbose: bool = False):
    
        if globType == "glob":
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
    def FindFiletype(self, desiredExts: list, directory: pathlib.Path = pathlib.Path.cwd(), verbose: bool = False):
        files = {}
        
        for file in self.scanDirectory():
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

    def findSisterFile(self, file: pathlib.Path, fileExt: str):
        se = self.regexExtraction(file, "seasonEpisode")
        fileList = self.FindFiletype([fileExt], file.parent)

        for item in fileList:
            regexFoundFile = self.regexExtraction(item, "seasonEpisode")
            if regexFoundFile:
                return item

        print("No sister file found.")
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
    
    validModes = ["submerge",
            "subtag",
            "organize",
            "rename",
            "interactive"]
    
    if programMode not in validModes:
        raise ValueError("Mode %r not found." % programMode)
    
    mainMessenger = messenger("mainThread")
    mainMessenger.programInit()
    mainMessenger.say("Program starting...")

    
    if programMode == "submerge":
        submerge(videoDir = viddir, subDir = subdir)

    fileOperator.scanDirectory(verbose=True)
    fileOperator.FindFiletype([".py", ".md", ".swp"], verbose=True)
    exit(0)
    

# ------------------------------------------------------------------------------------------------


def submerge(videoDir: pathlib.Path = pathlib.Path.cwd(), subDir: pathlib.Path = None):
    if subDir is None:
        subDir = videoDir

    print("Mode selected: submerge\n")
    print("Looking for files...")

    fileOperation = fileAuditor("submerge")
    
    videoFiles = fileOperation.scanDirectory(globPattern = "*.mkv", searchDir = videoDir, verbose=True)
    subFiles = fileOperation.scanDirectory(globPattern = "*.srt", searchDir = subDir, verbose=True)
    subFiles = fileOperation.scanDirectory(verbose=True)

    # merge subfile into mkv and set language to English
    # subprocess.run(["mkvmerge", "-o", str(outfile), str(srcfile), "--language", "0:eng", "--track-name", "0:English", "--default-track", "0:0", str(subfile)])

    # merge subfile into mkv and set language to English (.idx and .sub pairs)
    # subprocess.run(["mkvmerge", "-o", str(outfile), str(srcfile), "--language", "0:eng", "--track-name", "0:English", "--default-track", "0:0", str(subfile), str(subfile2])



if __name__ == "__main__":
    main()

