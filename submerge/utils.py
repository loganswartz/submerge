#!/usr/bin/env python3

# builtins
import pathlib


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

