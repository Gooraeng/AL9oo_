from __future__ import annotations
from typing import Sequence
from utils.config import vaild_formats


def _human_join(seq: Sequence[str], /, *, delimiter: str = ', ', final: str = 'or') -> str:
    size = len(seq)
    if size == 0:
        return ''

    if size == 1:
        return seq[0]

    if size == 2:
        return f'{seq[0]} {final} {seq[1]}'

    return delimiter.join(seq[:-1]) + f' {final} {seq[-1]}'


class InvaildFormat(TypeError):
    def __init__(self) -> None:
        vaild_formats_str = _human_join(vaild_formats, final='and')
        msg = f'The Format must be one of that : {vaild_formats_str}'
        super().__init__(msg)