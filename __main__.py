#!/usr/bin/env python3

"""Submerge.py: A tool for batch-merging discrete subtitle files into their
accompanying MKV video files.
"""

# builtin modules
import argparse
import pathlib
import subprocess
import shutil
import errno
import os
import re
import platform
import json

# 3rd party modules
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from langdetect import detect_langs

# my modules
from classes import messenger
from classes import operation



__author__ = "Logan Swartzendruber"
__version__ = "0.8"
__status__ = "Development"



# Wrapper for making paths from strings
def definePath(path: str):
    if path == None:
        return pathlib.Path.cwd()
    else:
        return pathlib.Path(path).resolve()

class SisterFileException(Exception):
    pass


def main():
    """
    Main loop of the program that configures and runs the desired operation.
    """


    cmdargparser = argparse.ArgumentParser(
            description=("A tool for batch-merging discrete subtitle files "
            "into their accompanying MKV video files, and other file "
            "manipulation."))
    
    cmdargparser.add_argument("-o",
                              "--operation",
                              help="set the file manipulation mode",
                              type=str,
                              default="interactive")
    cmdargparser.add_argument("-m",
                              "--mediadir",
                              help=("specify the directory containing media "
                              "files to operate on"),
                              type=pathlib.Path)
    cmdargparser.add_argument("-s", 
                              "--subdir",
                              help=("specify the directory containing "
                              "subtitles to operate on"),
                              type=pathlib.Path)
    cmdargparser.add_argument("-v",
                              "--verbose",
                              help="turn on verbose output",
                              action='store_true')
    
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
    
    if programMode == "submerge":
        submerge(videoDir = viddir, subDir = subdir)

    print()
    mainMessenger.say("Example of scanDirectory() on the CWD:")
    fileOperator.scanDirectory(verbose=True)
"""
    print()
    mainMessenger.say("Example of findFileType([\".py\", \".md\", \".swp\"]):")
    fileOperator.findFiletype([".py", ".md", ".swp"], verbose=True)
    print()
    
    mainMessenger.say(("Example of findSisterFile() looking for a sister or "
                       "type \".sh\" to \"submerge.py\":"))
    fileOperator.findSisterFile(
                        file=definePath("/home/logans/Submerge/submerge.py"),
                        validFileExts=[".sh"])
""" 
    

# ----------------------------------------------------------------------------


def submerge(videoDir: pathlib.Path = pathlib.Path.cwd(), subDir = None):
    """
    Merges subtitles into their matching video files.

    This operation works on a given directory containing mkv files. Based on
    those mkv files, it searches for potentially matching subtitle files in
    the same directory, child directories, or a specified alternative
    directory.

    There are 3 methods used to locate a subtitle file, and a failure to
    locate a file results in deferment to the next viable method:
        1. Searching for an exact filename match (with subtitle extension)
        2. Searching for a subtitle file with the same 'S__E__' qualifier
        3. Searching for a filename match with at least 75% similarity

    If a match is found, a subprocess call to 'mkvmerge' is initiated, and the
    files are merged. If an error occurs or there is no match, the error is
    logged and the operation continues on the next file.

    Finally, processed (input) files are moved to a different directory, the
    newly merged (output) files are placed into an output directory, and the
    program prints a report of the results of the operation.

    """

    if subDir is None:
        subDir = videoDir

    mergeOp = operation.fileOperation("submerge")
    print("Mode selected: submerge\n")
    print("Looking for files...")

    outDirectory = videoDir / "submerged"
    procDirectory = videoDir / "processed"
    outDirectory.mkdir(exist_ok=True)
    procDirectory.mkdir(exist_ok=True)

    videoFiles = mergeOp.scanDirectory(globPattern = "*.mkv",
                                       directory = videoDir,
                                       verbose=True)
    subFiles = mergeOp.findFiletype(desiredExts = [".srt",".ass",".ssa",".usf",
                                                   ".pgs",".idx",".sub"],
                                    directory = subDir,
                                    recursive=True,
                                    verbose=True)
    
    for srcfile in videoFiles:
        outfile = outDirectory / srcfile.name

        try:
            subfile = mergeOp.findSisterFile(srcfile, fileList=subFiles)
        except FileNotFoundError as e:
            mergeOp.recordFileError(errorFile=srcfile, errorStatus=e)
            mergeOp.messenger.say((f"findSisterFile() for {str(srcfile)} "
                                    "skipped.\n"))
            continue


        """
        If the subtitle file is a .idx file, we also have to merge in the
        matching .sub file, since those 2 together make up a single set of
        subtitles. To ensure we don't perform an operation twice on the same
        mkv, it always skips .sub files and always attempts to include .sub
        files when it operates on .idx files. Proper .idx/.sub pairs should
        always have identical names (aside from file extensions) in order to
        be properly detected, so we don't need to search for it at all.
        """
        if subfile.suffix == ".idx":
            subprocess.run(["mkvmerge", "-o", outfile, srcfile, "--language",
                            "0:eng", "--track-name", "0:English",
                            "--default-track", "0:0", subfile,
                            subfile.with_suffix(".sub")])
        elif subfile.suffix == ".sub":
            continue
        else:
            subprocess.run(["mkvmerge", "-o", outfile, srcfile, "--language",
                            "0:eng", "--track-name", "0:English",
                            "--default-track", "0:0", subfile])


        print()
        mergeOp.move(src, procDirectory, integrity_check=True)
    
    mergeOp.generateReport(processedDirectory=procDirectory,
                           outputDirectory=outDirectory)
    # submerge operation done


def subtag(videoDir: pathlib.Path() = pathlib.Path.cwd(),
           override_lang: str = ""):
    """
    Correctly tags the subtitle tracks of an mkv file.

    This operation takes a given mkv file (or set of mkv files), extracts
    all metadata from each file, and attempts to fill in (or fix) missing
    metadata.

    To do this, it analyzes the metadata pertaining to all contained subtitle
    tracks, and if a track with a 'language' field set to 'und' (undetermined),
    it dumps the subtitles and feeds them into langdetect, which determines
    the language of the subtitles and tags them as such.

    ISO639_1_to_ISO639_2() converts the language code used by langdetect
    (ISO 639-1 specifically) and converts it to the scheme used in the MKV
    standard (ISO 639-2). The 'langs' list is contains all the languages
    supported by langdetect out of the box, but more could be added by creating
    more language profiles if need be.

    """

    def ISO639_1_to_ISO639_2(langCode: str):
        langs = {
                "af":"afr",
                "ar":"ara",
                "bg":"bul",
                "bn":"ben",
                "ca":"cat",
                "cs":"ces",
                "cy":"cym",
                "da":"dan",
                "de":"deu",
                "el":"ell",
                "en":"eng",
                "es":"spa",
                "et":"est",
                "fa":"fas",
                "fi":"fin",
                "fr":"fra",
                "gu":"guj",
                "he":"heb",
                "hi":"hin",
                "hr":"hrv",
                "hu":"hun",
                "id":"ind",
                "it":"ita",
                "ja":"jpn",
                "kn":"kan",
                "ko":"kor",
                "lt":"lit",
                "lv":"lav",
                "mk":"mkd",
                "ml":"mal",
                "mr":"mar",
                "ne":"nep",
                "nl":"nld",
                "no":"nor",
                "pa":"pan",
                "pl":"pol",
                "pt":"por",
                "ro":"ron",
                "ru":"rus",
                "sk":"slk",
                "sl":"slv",
                "so":"som",
                "sq":"sqi",
                "sv":"swe",
                "sw":"swa",
                "ta":"tam",
                "te":"tel",
                "th":"tha",
                "tl":"tgl",
                "tr":"tur",
                "uk":"ukr",
                "ur":"urd",
                "vi":"vie",
                "zh-cn":"cmn", # this is actually ISO 639-3, might not work
                "zh-tw":"yue", # this is actually ISO 639-3, might not work
                }
        return(langs[langCode])

    tagOp = operation.fileOperation("subtag")

    # add timestamp to temp file to ensure unique folder
    timestamp = str(datetime.datetime.now()).split(" ")
    # replace illegal filename characters (for Windows)
    timestamp = timestamp[0]+"_"+".".join(timestamp[1].split(":"))

    extractionFolder = pathlib.Path("/tmp/submerge_" + timestamp + "/")
    extractionFolder.mkdir()
    if videoDir.is_dir():
        videoFiles = tagOp.scanDirectory(globPattern = "*.mkv",
                                         directory = videoDir,
                                         verbose=True)
    else:
        videoFiles = [videoDir]
    
    for srcfile in videoFiles:
        trackLangPairs = {}
        mkvmergeOutput = subprocess.run(["mkvmerge", "-J", srcfile])
        metadatajson = json.loads(mkvmergeOutput.stdout)
        
        """
        The following loop parses all tracks, records the track indexes of the
        subtitles, and then associates their documented language in the
        metadata with that track index.

        This step is essentially just auditing the file.
        """
        for track in metadatajson["tracks"]:
            if track["type"] == "subtitles":
                trackLangPairs[track["id"]] = track["properties"]["language"]
                tagOp.messenger.sayDictKey(dct=trackLangPairs,
                                           key=track["id"],
                                           keyLabel="Track")
        print(trackLangPairs)

        for track, lang in trackLangPairs:
            exportedSubTrack = pathlib.Path(f"{srcfile.name}-sub{track}")
            # iterate through tracks and look for those that are undefined.
            # then, extract those tracks to a file & read that into langdetect
            if trackLang == 'und':
                subprocess.run(["mkvextract",
                                srcfile,
                                "tracks",
                                f"{track}:{exportedSubTrack}"])
                
                """
                Read the extracted file into langdetect (mkvextract doesn't
                support outputting subtitle contents directly to stdout)
                """
                with open(exportedSubTrack) as subtitles:
                    determinedLang = detect(subtitles.read())

                # tag subtitle track with determinedLang
                subprocess.run(["mkvpropedit", srcfile, "--edit",
                                f"track:{track}", "--set",
                                f"language={determinedLang}"])
    
    # cleanup operation
    shutil.rmtree(extractionFolder)



if __name__ == "__main__":
    main()

