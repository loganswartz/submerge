import pathlib
import subprocess
import shutil
import errno
import os
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
from .messenger import messenger

class fileOperation(object):
    def __init__(self, opname: str):
        self.role = opname
        self.successCount = 0
        self.errorCount = 0
        self.errorFiles = {}
        self.messenger = messenger(self.role)

    # Returns a plain list of objects in the dir matching a glob (defaults: CWD, *)
    def scanDirectory(self, globPattern: str = "*", directory: pathlib.Path = pathlib.Path.cwd(), recursive: bool = False, verbose: bool = False):
    
        if not recursive:
            #########################
            files = [file for file in directory.glob(globPattern) if file.is_file()]
            # This is equivalent to:
            #
            # files = []
            # for file in directory.glob(globPattern):
            #     if file.is_file():
            #         files.append(file)
            #
            # (list comprehensions are confusing, man) 
            #########################
        else:
            files = [file for file in directory.rglob(globPattern) if file.is_file()]
        # recursive vs nonrecursive globbing, default is nonrecursive

        if verbose == True:
            print("Found: ")
            for file in files:
                print(file)
        return files

    # Pass this an array of file extensions (ie [".txt", ".mkv", etc...]), and it finds all files in a dir with those extensions and packs them into a dictionary
    def findFiletype(self, desiredExts: list, directory: pathlib.Path = pathlib.Path.cwd(), recursive: bool = False, verbose: bool = False):
        files = {}
        
        for file in self.scanDirectory(directory=directory, recursive=recursive):
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
            self.messenger.say("Extracted: " + result.group(regexResultGroup), indent=1)
            return result.group(regexResultGroup)
        else:
            return ""

    # nearly identical to findSisterFile, but you also pass it the output of findFiletype() instead of validFileExts, to prevent parsing the directory 1000x times or more for large operations (essentially just a 'Big O' improvement)
    def findSisterFile(self, file: pathlib.Path, validFileExts: list = None, fileList: list = None, indent: int = 0):
        # 1. find exact name match
        # 2. find SE match
        # 3. find fuzzy name match

        # get list of all files w/ valid filetype in the same directory (and child directories) as the input file
        if fileList == None:
            fileList = self.findFiletype(validFileExts, file.parent, recursive=True)
        if fileList == None and validFileExts == None:
            raise SisterFileException("Not enough information given to findSisterFile().")
        
        self.messenger.inform("Searching for sister file to " + str(file) + "...", indent=indent)
        # ------------------ 1 ------------------ #
        for filetype, array in fileList.items():
            if file.with_suffix(filetype) in array:
                self.messenger.say("Found ---> " + str(file.with_suffix(filetype)) + "\n", indent=indent+1)
                self.successCount += 1
                return file.with_suffix(filetype)
        
        self.messenger.say("Perfect match not found, resorting to SE search...", indent=indent+1)

        # ------------------ 2 ------------------ #
        # extracts the season/episode from the filename
        se = self.regexExtraction(file, "seasonEpisode")
        if se == "":
            self.messenger.say("SE not found, skipping SE search.", indent=indent+1)
        else:
            for filetype, array in fileList.items():
                for item in array:
                    if self.regexExtraction(item, "seasonEpisode") == se:
                        self.messenger.say("Found ---> " + str(file.with_suffix(filetype)) + "\n", indent=indent+1)
                        self.successCount += 1
                        return item
        self.messenger.say("SE match not found, resorting to best fuzzy match...", indent=indent+1)

        # ------------------ 3 ------------------ #
        bestMatch = [None, 0]
        for filetype, array in fileList.items():
            # hacky list comprehension to convert array of pathlib.Path objects to strings for compatability with fuzzywuzzy
            strArray = [str(file) for file in array]

            chosenFuzzyFile = process.extractOne(str(file.with_suffix(filetype)), strArray, scorer=fuzz.partial_ratio)
            if chosenFuzzyFile[1] > bestMatch[1]:
                bestMatch = chosenFuzzyFile

        if bestMatch[1] > 75:
            self.messenger.say("Found (STR: " + str(bestMatch[1]) + ") ---> " + str(bestMatch[0]) + "\n", indent=indent+1) 
            self.successCount += 1
            return pathlib.Path(bestMatch[0]).resolve()

        self.messenger.say("No sister file found.\n", indent=indent+1)
        # No sister file found with the exact same name, or with the same SE as the file, or one with over 75% fuzzy name match confidence
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(file.with_suffix(".subtitle")))


    def recordFileError(self, errorFile: pathlib.Path, errorStatus: str): 
        self.errorFiles[errorFile.name] = {"file": errorFile, "error": errorStatus}
        self.errorCount += 1
        self.messenger.sayError("Error on file " + errorFile.name + " was recorded.")

    def generateReport(self, processedDirectory: pathlib.Path, outputDirectory: pathlib.Path):
        self.messenger.operationReport(self.successCount, self.errorCount, self.errorFiles, processedDirectory, outputDirectory)

################################### copy or move?
    def moveFile(source: pathlib.Path, destination: pathlib.Path):
        try:
            shutil.copy2(str(source), str(destination))
        except (FileNotFoundError, shutil.Error) as error:
            self.recordFileError(errorFile=source, errorStatus=error, errorExtra=destination, errorExtraMeta="destination")
            print(error)
        except Exception as error:
            print("An unknown error occurred: " + error)

