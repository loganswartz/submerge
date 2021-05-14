#!/usr/bin/env python3

# Imports {{{
# builtins
import logging
import pathlib
import sys
import shutil

# 3rd party
import click

# local modules
from submerge.modules import handlers

# }}}


log = logging.getLogger("submerge")
log.setLevel(logging.INFO)
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
log.addHandler(sh)


@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
    }
)
@click.option("-v", "--verbose", is_flag=True)
def main(verbose):
    if verbose:
        log.setLevel(logging.DEBUG)

    # check for mkvtoolnix
    mkvtoolnix = ["mkvmerge", "mkvpropedit", "mkvextract", "mkvinfo"]
    missing_mkvtoolnix = [exec for exec in mkvtoolnix if not shutil.which(exec)]
    if missing_mkvtoolnix:
        print(f"{', '.join(missing_mkvtoolnix)} not found.")


for handler in handlers.values():
    main.add_command(handler)
