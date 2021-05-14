#!/usr/bin/env python3

# Imports {{{
# builtins
import pathlib
from importlib import import_module
import inspect
from typing import Mapping, Type

# 3rd party
import click

# }}}


# get all the python modules in this directory
directory = (
    pathlib.Path(inspect.getframeinfo(inspect.currentframe()).filename).resolve().parent
)
files = directory.glob("**/*.py")

blacklist = ["<stdin>", "base.py", "__init__.py", "__main__.py", "_template.py"]

modules = [
    module for module in files if module.is_file() and module.name not in blacklist
]


def get_handlers() -> Mapping[str, click.Command]:
    def relative_to_path(module: pathlib.Path, path: pathlib.Path):
        relative = module.relative_to(path).with_suffix("")
        as_import = str(relative).replace("/", ".")
        return as_import

    # dictionary version of __all__
    all = {
        module.stem: import_module(
            ".".join([__package__, relative_to_path(module, directory)])
        )
        for module in modules
    }

    def get_command_from_module(module):
        """
        Get an Handler subclass instance from a module.
        Get all objects from a module, and filter out all but the first Handler
        subclass found. Then return an instance of that class, or none if no
        subclass was found.
        """
        objects = module.__dict__.values()
        try:
            handler_cls = next(
                (obj for obj in objects if isinstance(obj, click.Command))
            )
            return handler_cls
        except StopIteration:  # no subclass found
            # print(f'No handler found in "{module.__name__}".')
            return None

    # a dict of Handler subclasses, indexed by the module they're from
    enabled = {
        name: get_command_from_module(module) for name, module in all.items()
    }
    # strip out modules that didn't have a handler
    handlers = {name: handler for name, handler in enabled.items() if handler}

    return handlers


handlers = get_handlers()
__all__ = ["handlers"]
