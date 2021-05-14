#!/usr/bin/env python3

# Imports {{{
# builtins
import logging

# 3rd party
import click

# local modules
from submerge.modules.base import Handler

# }}}


log = logging.getLogger(__name__)


@click.command()
def template():
    ...
