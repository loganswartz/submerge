#!/usr/bin/env python3

# Imports {{{
# builtins
import pathlib

# 3rd party
import click

# }}}


# https://stackoverflow.com/a/44349292


class DecoratorList(list):
    """
    Convenience class to easily combine and use multiple decorators.

    This class is mainly intended for use with click.option or click.argument
    decorators. When an instance of this class is used as a decorator, it
    applies every item inside it as a decorator to the passed function.
    """

    def __call__(self, func):
        for decorator in self:
            func = decorator(func)

        return func

    def as_params(self):
        """
        Automatically extract the raw click.Parameter objects from all
        decorators contained in the instance.
        """
        return [
            param
            for decorator in self
            for param in decorator(lambda: None).__click_params__
        ]

    def decorate(self, func):
        """
        Decorate an existing function.
        """
        func.params.extend(self.as_params())


path_args = DecoratorList(
    [
        click.argument(
            "paths", type=click.Path(exists=True, path_type=pathlib.Path), nargs=-1
        ),
        click.option(
            "-r", "--recursive", help="Recurse into subdirectories", is_flag=True
        ),
    ]
)
