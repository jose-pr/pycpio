__version__ = "0.0.1"

from zenlib.logging import loggify

from pathlib import Path
from typing import Union

from .cpioentry import CPIOEntry


@loggify
class PyCPIO:
    """
    A class for reading CPIO archives.
    """
    def __init__(self, *args, **kwargs):
        self.files = []

    def read_cpio(self, file_path: Union[str, Path]):
        """
        Reads a CPIO archive.
        """
        file_path = Path(file_path)

        self.logger.info("Reading CPIO archive: %s" % file_path)
        with open(file_path, 'rb') as f:
            self.raw_cpio = f.read()

        self.logger.info("[%s] Read bytes: %s" % (file_path, len(self.raw_cpio)))

        offset = 0
        while offset < len(self.raw_cpio):
            self.logger.debug("At offset: %s" % offset)
            header_data = self.raw_cpio[offset:offset + 110]
            entry = CPIOEntry(header_data, total_offset=offset, logger=self.logger, _log_init=False)
            offset += 110

            filename_data = self.raw_cpio[offset:offset + entry.namesize]
            entry.add_data(filename_data)
            offset += entry.get_name()

            if filesize := entry.filesize:
                file_data = self.raw_cpio[offset:offset + filesize]
                entry.add_data(file_data)
                offset += entry.read_contents()

            if entry.name == 'TRAILER!!!':
                break

            if len(self.raw_cpio) - offset < 110:
                if self.raw_cpio[offset:] == b'\x00' * (len(self.raw_cpio) - offset):
                    self.logger.info("Reached end of file.")
                else:
                    self.logger.warning("Detected data after trailer: %s" % self.raw_cpio[offset:])
                break
            self.files.append(entry)

    def list_files(self):
        """
        Returns a list of files in the CPIO archive.
        """
        return '\n'.join([f.name for f in self.files])

    def __str__(self):
        return "\n".join([str(f) for f in self.files])