
from io import IOBase
from zenlib.logging import loggify
from pycpio.cpio import pad_cpio
from pycpio.header import CPIOHeader, HEADER_NEW

from pathlib import Path


@loggify
class CPIOWriter:
    """
    Takes a list of CPIOData objects,
    writes them to the file specified by output_file.
    """
    def __init__(self, cpio_entries: list, structure=None, *args, **kwargs):
        self.cpio_entries = cpio_entries
        self.structure = structure if structure is not None else HEADER_NEW

    def write(self, output_file:Path|str):
        """
        Writes the CPIOData objects to the output file.
        """
        offset = 0
        self.logger.debug("Writing to: %s" % self.output_file)
        with Path(output_file).open("wb") as f:
            offset = self.write_fp(f)

        self.logger.info("Wrote %d bytes to: %s" % (offset, self.output_file))
    
    
    def write_fp(self, fp:IOBase):
        """
        Writes the CPIOData objects to the output file.
        """
        offset = 0
        for entry in self.cpio_entries.values():
            self.logger.log(5, "Writing entry: %s" % entry)
            entry_bytes = bytes(entry)
            padding = pad_cpio(len(entry_bytes))
            output_bytes = entry_bytes + b'\x00' * padding

            fp.write(output_bytes)
            self.logger.debug("[%d] Wrote '%d' bytes for: %s" % (offset, len(output_bytes), entry.header.name))
            offset += len(output_bytes)
        trailer = CPIOHeader(structure=self.structure, name="TRAILER!!!", logger=self.logger, _log_init=False)
        self.logger.debug("Writing trailer: %s" % trailer)
        fp.write(bytes(trailer))
        offset += len(bytes(trailer))
        return offset


