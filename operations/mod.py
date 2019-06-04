
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

