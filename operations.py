#!/usr/bin/env python3

"""Top-level file operations"""

__all__ = ['merge', 'tag', 'mod', 'audit']

# builtin modules
import pathlib
import subprocess
import shutil
import errno
import os
import re
import json
import difflib
import datetime

# 3rd party modules
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from langdetect import detect_langs, detect

# my modules
from submerge.objects import messenger
from submerge.objects.fileManipulator import fileManipulator
from submerge.utils import definePath, get_media_json


def merge(vidsrc: pathlib.Path = pathlib.Path.cwd(), subsrc = None):
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

    if subsrc is None:
        subsrc = vidsrc

    mergeOp = fileManipulator("merge")
    print("Mode selected: merge\n")
    print("Looking for files...")

    outDirectory = vidsrc / "merged"
    procDirectory = vidsrc / "processed"
    outDirectory.mkdir(exist_ok=True)
    procDirectory.mkdir(exist_ok=True)

    videoFiles = mergeOp.scanDirectory(globPattern = "*.mkv",
                                       directory = vidsrc,
                                       verbose=True)
    subFiles = mergeOp.findFiletype(desiredExts = [".srt",".ass",".ssa",".usf",
                                                   ".pgs",".idx",".sub"],
                                    directory = subsrc,
                                    recursive=True,
                                    verbose=True)

    for srcfile in videoFiles:
        outfile = outDirectory / srcfile.name

        try:
            subfile = mergeOp.findSisterFile(srcfile, fileList=subFiles)
        except FileNotFoundError as e:
            mergeOp.record_error(errorFile=srcfile, errorStatus=e)
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
        mergeOp.move(vidsrc, procDirectory, integrity_check=True)

    mergeOp.generateReport(processedDirectory=procDirectory,
                           outputDirectory=outDirectory)
    # merge operation done


def tag(vidsrc: pathlib.Path() = pathlib.Path.cwd(),
        audio_langs = None,
        subs_langs = None,
        force_check: bool = False,
        verbose: bool = False):
    """
    Correctly tags the subtitle tracks of an mkv file.

    This operation takes a given mkv file (or set of mkv files), extracts
    all metadata from each file, and attempts to fill in (or fix) missing
    metadata.

    To do this, it analyzes the metadata pertaining to all contained subtitle
    tracks, and if a track with a 'language' field set to 'und' (undetermined),
    it dumps the subtitles and feeds them into langdetect, which determines
    the language of the subtitles and tags them as such.

    If subs_lang is set, the specified langs will be written to the specified
    tracks. If force_check is set to True, all subtitle tracks will be parsed
    by langdetect, regardless of metadata tags. Useful if you think a track has
    been incorrectly tagged.

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

    # setup for operation
    # add timestamp to temp file to ensure unique folder
    # replace illegal filename characters (for Windows)
    tagOp = fileManipulator("tag")
    timestamp = str(datetime.datetime.now()).split(" ")
    timestamp = timestamp[0]+"_"+".".join(timestamp[1].split(":"))

    extractionFolder = definePath("/tmp/merge_" + timestamp + "/")
    extractionFolder.mkdir()

    # find/set files to operate on
    if vidsrc.is_dir():
        videoFiles = tagOp.scanDirectory(globPattern = "*.mkv",
                                         directory = vidsrc,
                                         verbose=True)
    else:
        # if it's just a file, we simply put in in an array by itself
        videoFiles = [vidsrc]


    # process the files
    for srcfile in videoFiles:
        trackLangPairs = {}
        # get metadata tags from media file
        mediaJSON = get_media_json(srcfile)

        # add manual overrides
        tagCMD = propeditCommand(mkvpropedit, srcfile)
        if audio_langs != None:
            for track, lang in audio_langs.items():
                tagCMD.set_track_lang(track, lang)
        if subs_langs != None:
            for track, lang in subs_langs.items():
                tagCMD.set_track_lang(track, lang)

        """
        The following loop parses all tracks, records the track indexes of the
        subtitles, and then associates their documented language in the
        metadata with that track index.

        This step is essentially just auditing the file.
        """
        for track in mediaJSON["tracks"]:
            if track["type"] == "subtitles":
                # create dict entry (key = track id, value = language)
                trackLangPairs[track["id"]] = track["properties"]["language"]
                if verbose:
                    tagOp.messenger.sayDictKey(dct=trackLangPairs,
                                               key=track["id"],
                                               keyLabel="Track")
        if verbose:
            print(trackLangPairs)


        for track, lang in trackLangPairs.items():
            # iterate through tracks and look for those that are undefined.
            # then, extract those tracks to a file & read that into langdetect
            extractCMD = extractCommand("mkvextract", srcfile)
            if (lang == 'und' and subs_lang == None) or
                (force_check):

                exportedSubTrack = pathlib.path(f"{srcfile.name}-sub{track}")
                extractCMD.add_track(track,extractionFolder / exportedSubTrack)
                extractCMD.run()

                """
                Read the extracted file into langdetect (mkvextract doesn't
                support outputting subtitle contents directly to stdout)
                """
                with open(exportedSubTrack) as subtitles:
                    determinedLang = detect(subtitles.read())
                newLang = ISO639_1_to_ISO639_2(determinedLang)

                # tag subtitle track with determinedLang
                subprocess.run(["mkvpropedit", srcfile, "--edit",
                                f"track:{track+1}", "--set",
                                f"language={newLang}"])
            elif lang == 'und' and subs_lang != None:

                # tag subtitle track with subs_lang
                subprocess.run(["mkvpropedit", srcfile, "--edit",
                                f"track:{track+1}", "--set",
                                f"language={subs_lang[track]}"])

            else:
                tagOp.messenger.say((f"Track language is set to {lang}, no "
                            "need to change. Proceeding to next file..."))

    # cleanup operation
    shutil.rmtree(extractionFolder)


def mod(dfAudio: str, dfSubs: str):
    modOp = operation.fileOperation("mod")

    # add timestamp to temp file to ensure unique folder
    timestamp = str(datetime.datetime.now()).split(" ")
    # replace illegal filename characters (for Windows)
    timestamp = timestamp[0]+"_"+".".join(timestamp[1].split(":"))

    extractionFolder = pathlib.Path("/tmp/merge_" + timestamp + "/")
    extractionFolder.mkdir()
    if videoDir.is_dir():
        videoFiles = modOp.scanDirectory(globPattern = "*.mkv",
                                         directory = videoDir,
                                         verbose=True)
    else:
        videoFiles = [videoDir]

    for srcfile in videoFiles:
        trackLangPairs = {}
        mediaJSON = get_media_json(srcfile)

        """
        The following loop parses all tracks, records the track indexes of the
        subtitles, and then associates their documented language in the
        metadata with that track index.

        This step is essentially just auditing the file.
        """
        for track in mediaJSON["tracks"]:
            if track["type"] == "subtitles":
                trackLangPairs[track["id"]] = track["properties"]["language"]
                modOp.messenger.sayDictKey(dct=trackLangPairs,
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


def audit(vidsrc: pathlib.Path = pathlib.Path.cwd(), recursive: bool = True):
    """
    Scan a directory and audit all the files in it, noting any issues that
    could be fixed.

    No subtitles found
    Discrete subtitles that could be integrated
    Subtitle tracks set as 'und'
    Mislabelled resolution

    Issues that are audited include untagged subtitle tracks, no detected
    subtitles, etc
    """
    auditOp = fileManipulator("audit")

    strings = auditOp.scanDirectory(directory=vidsrc)
    diff = []
    for index, name in enumerate(strings):
        if index >= (len(strings)-1):
            diff.append([i for i,j in enumerate(difflib.ndiff(str(strings[index]), str(strings[0]))) if j[0] != ' '])
        else:
            diff.append([i for i,j in enumerate(difflib.ndiff(str(strings[index]), str(strings[index+1]))) if j[0] != ' '])

    diffset = set()
    for i in diff:
        diffset = diffset.union(set(i))
    totaldiff = list(diffset)

    print("test")


def rename(vidsrc: pathlib.Path, pattern: str):
    """
    Batch rename a set of files based on a pattern
    """

    """
    ops = [["move", [0,14], "end"], ["insert", 0, "test "], ["delete", [32,35]], ["replace", [36,38]]]

    string = "[HorribleSubs] Sword Art Online II - 01 [1080p].mkv"
    for i in ops:
        if ops[i][0] == "move":

            return string[ops[i][1][0]:ops[i][1][1]]
        elif ops[i][0] == "insert":
            pass
        elif ops[i][0] == "delete":
            pass
        elif ops[i][0] == "replace":
            pass

    operations:
        insert
        delete
        replace
        increment number
    """


    def insert(regex: str, insertPoint: int, insertVal:str, inString: str):
        result = re.sub(regex, "\\1" + insertVal + "\\"+str(insertPoint), inString)
        return result

    def delete(regex: str, replacePoint: int, replaceVal:str, inString: str):
        result = re.sub(regex, "\\1" + replaceVal + "\\"+str(replacePoint+1), inString)
        return result

    def replace(regex: str, replacePoint: int, replaceVal:str, inString: str):
        result = re.sub(regex, "\\1" + replaceVal + "\\"+str(replacePoint+1), inString)
        return result

    def increment(regex: str, replacePoint: int, replaceVal:str, inString: str):
        result = re.sub(regex, "\\1" + replaceVal + "\\"+str(replacePoint+1), inString)
        return result


    regex = r"^((((\w)+\s?)+)\s(is)\s)((((\w)+\s?)+))$"
    index = 6
    string = "this is a test sentence"
    print(insert(regex, index, "not ", string))

    regex = r"(\[HorribleSubs\] Sword Art Online II)( - 01 \[1080p\]\.mkv)"
    index = 2
    string = "[HorribleSubs] Sword Art Online II - 01 [1080p].mkv"
    print(insert(regex, index, " not", string))

    """
    regex = r"^((\s?(\w)+\s?)+)(is)((\s?(\w)+\s?)+)$"
    index = 4
    string = "this is a test sentence"
    print(replace(regex, index, "not", string))
    """
