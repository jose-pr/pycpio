"""
CPIO directory object
"""

from typing import Unpack

from .data import CPIOData, CPIODataKwargs


class CPIO_Dir(CPIOData):
    """
    Directory object
    """

    def __init__(self, *args, **kwargs: Unpack[CPIODataKwargs]):
        super().__init__(*args, **kwargs)
        if path := kwargs.pop("path", None):
            path = path.resolve()
            self.header.mode = int(self.header.mode, 16) | (path.stat().st_mode & 0o777)
            self.header.mtime = path.resolve().stat().st_mtime
            if path.is_absolute():
                self.header.name = str(path.relative_to(path.anchor))

        if name := kwargs.pop("name", None):
            self.header.name = name
