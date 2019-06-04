#!/usr/bin/env python3

# builtin modules
import pathlib
import subprocess
import shutil
import errno
import os
import re

# 3rd party modules
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# my modules
from .messenger import messenger
from .hashObject import getHash


class fileManipulator(object):
    """
    Object to perform file operations.

    An instance of this object should be used for all file operations, as it
    has some useful methods and built-in error recording for when those methods
    fail.

    """

    def __init__(self, opname: str):
        self.role = opname
        self.successCount = 0
        self.errorCount = 0
        self.errorFiles = {}
        self.messenger = messenger(self.role)


    def parse_dir(self,
                      globPattern: str = "*",
                      directory: pathlib.Path = pathlib.Path.cwd(),
                      recursive: bool = False,
                      verbose: bool = False):
        """
        Returns an array of file objects (in pathlib.Path objects) in the given
        dir that match a glob.

        Defaults to the CWD, and a '*' glob.
        """

        if not recursive:
            files = [i for i in directory.glob(globPattern) if i.is_file()]
            """
            For those of you confused by list comprehensions (me), this is
            equivalent to:

            files = []
            for file in directory.glob(globPattern):
                if file.is_file():
                    files.append(file)

            """
        else:
            files = [i for i in directory.rglob(globPattern) if i.is_file()]

        if verbose == True:
            print("Found: ")
            for file in files:
                print(file)
        return files


    def find_type(self,
                     desiredExts: list,
                     directory: pathlib.Path = pathlib.Path.cwd(),
                     recursive: bool = False,
                     verbose: bool = False):
        """
        Searches a directory for files of the desired type.

        This method calls parse_dir() and sorts out the desired files. It
        sorts based on an array of given file extensions such as:
        [".txt", ".mkv", ".pkg"]

        It then creates a dictionary where the key is the file extension, and
        the value is an array of all files found with that extension. This is
        only ever so slightly more complicated than a flat array, and allows
        us to easily use certain filetypes without reparsing the array.

        """

        files = {}

        for file in self.parse_dir(directory=directory,
                                       recursive=recursive):
            if file.suffix in desiredExts:
                try:
                    files[file.suffix].append(file)
                except KeyError as error:
                    files[file.suffix] = []
                    files[file.suffix].append(file)

        """
        Above is a better implementation of the commented code below, the top
        only makes 1 pass over all files in the directory, whereas the simpler
        code shown below makes n passes over all the files, where n is the
        number of extensions you are looking for

        #########################
        for ext in desiredExts:
            files[ext] = self.parse_dir(globPattern="*" + ext)
        #########################

        """

        if verbose == True:
            print("Found: ")
            for filetype, filelist in files.items():
                print(filetype + " --> " + str(filelist))
        return files


    def regex_extract(self,
                        file: pathlib.Path,
                        regexName: str,
                        regexResultGroup: int = 0):
        """
        Extracts info from a given filename based on a selected regex.

        For future expansion, I've made the function fetch the regex it will
        use from regexList, so if need be, more regular expressions can be
        easily added and used.

        """

        regexList = {
                    "seasonEpisode":
                        {
                        "regex":r"[s|S]\d{1,3}\s?[e|E]\d{1,3}",
                        "captureGroup":0  # desired capture group to return
                        }
                    }

        regex = re.compile(regexList.get(regexName).get("regex"))

        result = re.search(regex, file.name)
        if result:
            self.messenger.say(f"Extracted: {result.group(regexResultGroup)}",
                               indent=1)
            return result.group(regexResultGroup)
        else:
            return ""


    def find_sister(self,
                       file: pathlib.Path,
                       validFileExts: list = None,
                       fileList: list = None,
                       indent: int = 0):
        """
        Finds a matching subtitle file for some given file[s].

        This function attempts to search for a subtitle file that matches some
        given file[s], using these 3 different approaches (in the order shown):

        1. Exact name matching
        2. S__E__ scheme matching
        3. Fuzzy name matching

        Exact name matching is the first method used to find a match and it's
        pretty self-explanatory: it finds a subtitle file with the exact same
        filename as the given video file.

        S__E__ scheme matching is simply matching based on the recorded season
        and episode number (found in the filename). If both a found subtitle
        file and the input video file have the same season and episode number,
        then they are matched. If a season/episode number isn't found in
        the filename, this method is skipped.

        Fuzzy name matching uses the fuzzywuzzy Python module to perform fuzzy
        matching, and considers a match to be 2 filenames that match at more
        than 75% similarity.

        You can pass this method the output of find_type() (an array of
        pathlib.Path objects) instead of the validFileExts array to prevent
        parsing the directory 1000x times or more for large operations
        (essentially just a 'Big O' improvement).

        """

        fuzzyMatchMinimum = 75


        if fileList == None and validFileExts == None:
            raise SisterFileException(("Not enough information given to"
                                        "find_sister()."))
        if fileList == None:
            fileList = self.find_type(validFileExts, file.parent,
                                         recursive=True)

        self.messenger.inform(f"Searching for sister file to {str(file)}...",
                              indent=indent)

        # ------------------ 1 ------------------ #
        for filetype, array in fileList.items():
            if file.with_suffix(filetype) in array:
                self.messenger.say(("Found ---> "
                                    f"{str(file.with_suffix(filetype))}\n"),
                                    indent=indent+1)
                self.successCount += 1
                return file.with_suffix(filetype)


        self.messenger.say(("Perfect match not found, deferring to SE "
                            "search..."), indent=indent+1)

        # ------------------ 2 ------------------ #
        se = self.regex_extract(file, "seasonEpisode")
        if se == "":
            self.messenger.say("SE not found, skipping SE search.",
                               indent=indent+1)
        else:
            for filetype, array in fileList.items():
                for item in array:
                    if self.regex_extract(item, "seasonEpisode") == se:
                        self.messenger.say("Found ---> " +
                                           str(file.with_suffix(filetype)) +
                                           "\n",
                                           indent=indent+1)
                        self.successCount += 1
                        return item

        self.messenger.say("SE match not found, deferring to fuzzy match...",
                           indent=indent+1)

        # ------------------ 3 ------------------ #
        bestMatch = [None, 0]

        for filetype, array in fileList.items():

            strArray = [str(file) for file in array]
            """
            List comprehension to convert array of pathlib.Path objects to
            array of strings for compatability with fuzzywuzzy module
            """

            chosenFuzzyFile = process.extractOne(
                                    str(file.with_suffix(filetype)),
                                    strArray,
                                    scorer=fuzz.partial_ratio)

            if chosenFuzzyFile[1] > bestMatch[1]: # compare similarity ratings
                bestMatch = chosenFuzzyFile

        if bestMatch[1] > fuzzyMatchMinimum:
            self.messenger.say((f"Found (Strength: {str(bestMatch[1])}) ---> "
                                f"{str(bestMatch[0])}\n"),
                                indent=indent+1)

            self.successCount += 1
            return pathlib.Path(bestMatch[0]).resolve()


        self.messenger.say("No sister file found.\n", indent=indent+1)

        """
        If we reached this point, all search methods failed to find a match,
        so we throw a FileNotFoundError that will get logged.
        """
        raise FileNotFoundError(errno.ENOENT,
                                os.strerror(errno.ENOENT),
                                str(file.with_suffix(".subtitle")))


    def record_error(self, errorFile: pathlib.Path, errorStatus: str): 
        """
        Records file errors that occur during a file operation.
        """

        self.errorFiles[errorFile.name] = {"file": errorFile,
                                           "error": errorStatus}
        self.errorCount += 1
        self.messenger.sayError(f"An error on {errorFile.name} was recorded.")


    def gen_report(self, processedDirectory: pathlib.Path,
                       outputDirectory: pathlib.Path):
        """
        Wrapper function for messenger.operationReport() so that some variables
        (everything but processedDirectory and outputDirectory) don't need to
        be explicitly passed.
        """
        self.messenger.operationReport(self.successCount,
                                       self.errorCount,
                                       self.errorFiles,
                                       processedDirectory,
                                       outputDirectory)


    def move(self,
             source: pathlib.Path,
             destination: pathlib.Path,
             integrity_check: bool = True):
        """
        Wrapper function for shutil.move() that adds file integrity checks.

        If integrity_check is True, shutil.move() is called with copy_function
        set to my custom copy3() method instead of the default shutil.copy2().
        Otherwise, it simply calls shutil.move() with the default copy2().

        Also adds error recording.
        """

        try:
            if integrity_check == True:
                shutil.move(source, destination, copy_function=copy3)
            else:
                shutil.move(source, destination)
        except (FileNotFoundError, shutil.Error) as error:
            self.record_error(errorFile=source,
                              errorStatus=error,
                              errorExtra=destination,
                              errorExtraMeta="destination")
            print(error)
        except Exception as error:
            print("An unknown error occurred: " + error)


    def copy3(self, src: pathlib.Path, dst: pathlib.Path):
        """
        Wrapper of shutil.copy2() that adds file hashing to check for file
        integrity.

        This function hashes src, attempts to copy the file object to dst, and
        then hashes the dst file and compares the hashes. If they don't match,
        the dst file is thrown out and it tries again.

        After <maxAttempts> failures, the operation aborts.

        """

        maxAttempts = 3
        attempts = 0

        # Initial copy and hashing.
        preCopyHash = hashObject.getHash(src)
        shutil.copy2(src, dst)
        postCopyHash = hashObject.getHash(dst)

        while preCopyHash != postCopyHash and attempts < maxAttempts:
            """
            If the hashes don't match, retry until they do match or maxAttempts
            is reached.
            """

            # Delete corrupted dst
            if src.is_dir():  
                shutil.rmtree(dst)
            elif src.is_file():
                dst.unlink()

            # Copy again and rehash
            shutil.copy2(str(src), str(dst))
            postCopyHash = hashObject.getHash(dst)

            attempts += 1

        if preCopyHash == postCopyHash:
            return dst  # copy2() returns dst on success, so this does too.
        else:
            raise Exception(("Max number of copy attempts was made, "
                             "operation aborted."))

