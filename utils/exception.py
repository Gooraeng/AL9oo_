from __future__ import annotations
from config import vaild_formats
from inspect import cleandoc
from typing import Sequence
from .check import _match_check
from .models import ReferenceTypes, SearchTypes

import discord


def _human_join(seq: Sequence[str], /, *, delimiter: str = ', ', final: str = 'or') -> str:
    size = len(seq)
    if size == 0:
        return ''

    if size == 1:
        return seq[0]

    if size == 2:
        return f'{seq[0]} {final} {seq[1]}'

    return delimiter.join(seq[:-1]) + f' {final} {seq[-1]}'


def key(interaction : discord.Interaction):
    return interaction.guild


class AlgooError(Exception):
    """Basic Exception For AL9oo."""
    pass


class LoadingFailedMongoDrive(AlgooError):
    def __init__(self) -> None:
        self.message = 'Failed Loading Mongo driver.'
        super().__init__(self.message)
        
        
class DownloadFailed(AlgooError):
    """Raised When downloading reference failed"""
    def __init__(self, filename : str) -> None:
        self.message = f'Downloading Reference for {filename} was failed.'
        super().__init__(self.message)


class SearchFailedBasic(AlgooError):
    """Basic Exception failure for search"""
    def __init__(
        self,
        type : ReferenceTypes
    ) -> None:
        self.message = cleandoc(
            f"""Sorry, There was unknown error while searching {type.upper()} reference.
            Please consider what you wrote.
            """
        )
        super().__init__(self.message)


class SearchFailed(AlgooError):
    """Raised when there's no any result or failed to find."""
    def __init__(
        self,
        type : SearchTypes,
        find : str,
        original_list : list
    ) -> None:
        result = _match_check(text=find, original_list=original_list)
        if result and len(result) > 0 :
            result = '\n\nDid you mean...\n' + '\n'.join(f'`{s}`' for s in result)
        else:
            result = ''
        self.message = f'Failed to find {type} `{find}`{result}'
        super().__init__(self.message)


class NotFilledRequiredField(AlgooError):
    """Raised when you didn't fill required field."""
    def __init__(self, msg : str) -> None:
        self.message = msg
        super().__init__(msg)


class ButtonOnCooldown(discord.ext.commands.CommandError):
    def __init__(self, retry_after : float) -> None:
        self.retry_after = retry_after


class InvaildFileFormat(TypeError):
    def __init__(self) -> None:
        vaild_formats_str = _human_join(vaild_formats, final='and')
        self.msg = f'The Format must be one of that : {vaild_formats_str}'
        super().__init__(self.msg)