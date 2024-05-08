from io import IOBase
from pathlib import Path
from typing import Union

from pycpio.cpio import CPIOArchive, CPIOData, pad_cpio
from pycpio.header import CPIOHeader

from ..common import Logged


class CPIOReader(Logged):
    """
    A class for reading CPIO archives.
    """

    def __init__(self, stream: IOBase, overrides={}, **kwargs):
        super().__init__(**kwargs)
        self.stream = stream
        self.overrides = overrides
        self.entries = CPIOArchive(
            logger=self.logger,
        )
        self.offset = 0

    def _read_bytes(self, num_bytes: int, pad=False) -> bytes:
        """Reads num_bytes from self.raw_cpio, starting at self.offset."""
        data: bytes = b""
        read = 0
        while read < num_bytes:
            data += self.stream.read(num_bytes - read)
            _read = len(data)
            if not _read:
                raise EOFError
            read = _read
        self.offset += read
        if len(data) > 256:
            self.logger.debug(
                "Read %s bytes: %s...%s" % (num_bytes, data[:128], data[-128:])
            )
        else:
            self.logger.debug("Read %s bytes: %s" % (num_bytes, data))

        if pad:
            pad_size = pad_cpio(read)
            self.logger.debug("Padding offset by %s bytes" % pad_size)

        return data

    def read_header(self) -> CPIOHeader:
        """Processes a single CPIO header from self.raw_cpio."""
        header_data = self._read_bytes(110)

        try:
            header = CPIOHeader(header_data, self.overrides, logger=self.logger)
        except ValueError as e:
            self.logger.error("Failed to process header: %s" % e)
            self.logger.info(
                "[%s] Header data at offset %d: %s"
                % (self.stream, self.offset, header_data)
            )
            return

        # Get the filename now that we know the size
        filename_data = self._read_bytes(int(header.namesize, 16), pad=True)
        header.add_data(filename_data)
        header.get_name()

        # If it's the trailer, break
        if not header.mode_type:
            self.logger.info("Trailer detected at offset: %s" % self.offset)
            return
        return header

    def read_data(self, header: CPIOHeader | int):
        datasize = header if isinstance(header, int) else int(header.filesize, 16)
        return self._read_bytes(datasize, pad=True)

    def read_entry(self, stop_at_trailer=True):
        """Processes the file object self.cpio_file, yielding CPIOData objects."""
        trailer = False
        while True:
            try:
                self.logger.debug("At offset: %s" % self.offset)
                if header := self.read_header():
                    trailer = False
                    yield CPIOData.get_subtype(
                        data=self.read_data(header),
                        header=header,
                    )
                elif stop_at_trailer:
                    break
            except EOFError:
                if not trailer:
                    self.logger.warning("Reached end of file without finding trailer")

    def __next__(self):
        yield from self.read_entry(False)

    def __iter__(self):
        return self
