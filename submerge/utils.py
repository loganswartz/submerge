#!/usr/bin/env python3

# builtins
import pathlib
from math import floor


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

def pretty_time_delta(seconds):
    _seconds = int(seconds)
    days, _seconds = divmod(_seconds, 86400)
    hours, _seconds = divmod(_seconds, 3600)
    minutes, _seconds = divmod(_seconds, 60)
    seconds = seconds - float((days*86400)+(hours*3600)+(minutes*60))
    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds:.0f}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds:.0f}s"
    elif minutes > 0:
        return f"{minutes}m {seconds:.1f}s"
    else:
        return f"{seconds:.2f}s"

def get_docstring(obj):
    if obj.__doc__:
        lines = [line.strip() for line in obj.__doc__.split('\n') if line.strip()]
        return lines[0]
    else:
        return None

