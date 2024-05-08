from io import IOBase
from typing import Iterable, Mapping, Unpack

from ..common import Logged, LoggedKwargs
from ..cpio import pad_cpio
from ..cpio.data import CPIOData, CPIODataKwargs
from ..header import HEADER_NEW, CPIOHeader
from ..masks import CPIOModes


class CPIOWriter(Logged):
    """
    Takes a list of CPIOData objects,
    writes them to the file specified by output_file.
    """

    def __init__(self, stream: IOBase, structure=None, **kwargs: Unpack[LoggedKwargs]):
        super().__init__(**kwargs)
        self.stream = stream
        self.structure = structure if structure is not None else HEADER_NEW

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def write(self, data: CPIOData | Iterable[CPIOData] | Mapping[str, CPIOData]):
        """
        Writes the CPIOData objects to the output stream.
        """
        offset = 0
        iter = [data] if isinstance(data, (CPIOData, CPIOHeader)) else data
        if isinstance(data, Mapping):
            iter: Iterable[CPIOData] = data.values()
        for entry in iter:
            self.logger.log(5, "Writing entry: %s" % entry)
            entry_bytes = bytes(entry)
            padding = pad_cpio(len(entry_bytes))
            output_bytes = entry_bytes + b"\x00" * padding
            self.stream.write(output_bytes)
            self.logger.debug(
                "[%d] Wrote '%d' bytes for: %s"
                % (offset, len(output_bytes), entry.name)
            )
            offset += len(output_bytes)
        return offset

    def close(self, close_stream=False):
        """
        Writes the CPIOData objects to the output stream.
        """
        written = self.write(
            CPIOHeader(
                structure=self.structure,
                name="TRAILER!!!",
                logger=self.logger,
            )
        )
        if close_stream:
            self.stream.close()
        return written

    def add_entry(
        self, mode: CPIOModes, name: str, data=b"", **kwargs: Unpack[CPIODataKwargs]
    ):

        kwargs.update(structure=self.structure, logger=self.logger)

        self.write(
            CPIOData.create_entry(
                name=name,
                mode=mode.value,
                data=data,
                **kwargs,
            )
        )
