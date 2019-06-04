from submerge.objects.messenger import messenger

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
    """


    # setup for operation
    # add timestamp to temp file to ensure unique folder
    # replace illegal filename characters (for Windows)
    tagOp = fileManipulator("tag")


    # find/set files to operate on
    if vidsrc.is_dir():
        videoFiles = tagOp.scanDirectory(globPattern = "*.mkv",
                     directory = vidsrc, verbose=True)
    else:
        # if it's just a file, we simply put in in an array by itself
        videoFiles = [vidsrc]


    # process the files
    for srcfile in videoFiles:

        # get metadata tags from media file
        mediaJSON = get_media_json(srcfile)
        trackLangPairs = gen_track_lang_dict(mediaJSON)


        # create tag command and add manual overrides
        tagCMD = propeditCommand(mkvpropedit, srcfile)
        if audio_langs != None:
            for track, lang in audio_langs.items():
                tagCMD.set_track_lang(track, lang)
        if subs_langs != None:
            for track, lang in subs_langs.items():
                tagCMD.set_track_lang(track, lang)


        for track, lang in trackLangPairs.items():
            # iterate through tracks and look for those that are undefined.
            # then, extract those tracks to a file & read that into langdetect
            extractCMD = extractCommand("mkvextract", srcfile)

            if (lang == 'und' and subs_lang == None) or
                (force_check):
                # tag subtitle track with determinedLang
                newLang = determine_lang(srcfile, track)
                tagCMD.set_track_lang(track, newLang)

            elif lang == 'und' and subs_lang != None:
                # tag subtitle track with subs_lang
                tagCMD(track, subs_lang[track])

            else:
                tagOp.messenger.say((f"Track language is set to {lang}, no "
                            "need to change. Proceeding to next file..."))

    tagCMD.run()
    # cleanup operation
    shutil.rmtree(extractionFolder)


def ISO639_1_to_ISO639_2(langCode: str):
    """
    ISO639_1_to_ISO639_2() converts the language code used by langdetect
    (ISO 639-1 specifically) and converts it to the scheme used in the MKV
    standard (ISO 639-2). The 'langs' list is contains all the languages
    supported by langdetect out of the box, but more could be added by creating
    more language profiles if need be.

    """
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


def gen_track_lang_dict(tag_json: dict):
    """
    The following loop parses all tracks, records the track indexes of the
    subtitles, and then associates their documented language in the
    metadata with that track index.

    This step is essentially just auditing the file.
    """
    messenger = messenger("gen_dict")

    trackLangPairs = {}
    for track in mediaJSON["tracks"]:
        if track["type"] == "subtitles":
            # create dict entry (key = track id, value = language)
            trackLangPairs[track["id"]] = track["properties"]["language"]
            if verbose:
                messenger.sayDictKey(dct=trackLangPairs,
                                key=track["id"], keyLabel="Track")

    if verbose:
        print(trackLangPairs)

    return trackLangPairs


def determine_lang(src: pathlib.Path, track: int):

    # create temp folder and extract sub track to folder
    extractionFolder = definePath("/tmp/submerge_" + gen_rand_string() + "/")
    extractionFolder.mkdir()
    exportedSubTrack = pathlib.path(gen_rand_string())
    extractCMD.add_track(track, extractionFolder / exportedSubTrack)
    extractCMD.run()

    """
    Read the extracted file into langdetect (mkvextract doesn't
    support outputting subtitle contents directly to stdout)
    """
    with open(exportedSubTrack) as subtitles:
        determinedLang = detect(subtitles.read())
    newLang = ISO639_1_to_ISO639_2(determinedLang)

    return newLang

