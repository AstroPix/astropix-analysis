# Copyright (C) 2025 the astropix team.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""File I/O for the astropix chip.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import struct
import typing

import astropy.table

from astropix_analysis import logger
from astropix_analysis.fmt import AbstractAstroPixReadout


class FileHeader:

    """Class describing a file header.

    The content of the header can be literally anything that is json-serializable,
    i.e., the only request that we make is that ``json.dumps(self._content)``
    is not raising an exception.

    The basic contract is that when the ``write()`` method is called we write
    into the output binary file:

    * the header magic number;
    * the length of the header content in bytes;
    * the actual header content.

    In the opposite direction, when the ``read()`` hook is called, we do:

    * read the first small chunk of the binary file and make sure the magic number is correct;
    * read the header length;
    * read and deserialize the header content, returning a full fledges ``FileHeader`` object.

    Arguments
    ---------
    content : anything that is serializable
        The header content.
    """

    MAGIC_NUMBER = '%APXDF'
    _HEADER_LENGTH_FMT = 'I'
    ENCODING = 'utf-8'

    def __init__(self, content: typing.Any) -> None:
        """Constructor.
        """
        self._content = content

    def write(self, output_file: typing.BinaryIO) -> None:
        """Serialize the header structure to an output binary file.

        Arguments
        ---------
        output_file : BinaryIO
            A file object opened in "wb" mode.
        """
        data = json.dumps(self._content).encode(self.ENCODING)
        output_file.write(self.MAGIC_NUMBER.encode(self.ENCODING))
        output_file.write(struct.pack(self._HEADER_LENGTH_FMT, len(data)))
        output_file.write(data)

    @classmethod
    def read(cls, input_file: typing.BinaryIO) -> 'FileHeader':
        """De-serialize the header structure from an input binary file.

        Arguments
        ---------
        input_file : BinaryIO
            A file object opened in "rb" mode.
        """
        magic = input_file.read(len(cls.MAGIC_NUMBER)).decode(cls.ENCODING)
        if magic != cls.MAGIC_NUMBER:
            raise RuntimeError(f'Invalid magic number ({magic}), expected {cls.MAGIC_NUMBER}')
        header_length = input_file.read(struct.calcsize(cls._HEADER_LENGTH_FMT))
        header_length = struct.unpack(cls._HEADER_LENGTH_FMT, header_length)[0]
        content = json.loads(input_file.read(header_length).decode(cls.ENCODING))
        return cls(content)

    def __eq__(self, other: 'FileHeader') -> bool:
        """Comparison operator---this is useful in the unit tests in order to make
        sure that the serialization/deserialization roundtrips.
        """
        return self._content == other._content

    def __str__(self) -> str:
        """String representation.
        """
        return f'{self._content}'


class AstroPixBinaryFile:

    """Class describing a binary file containing packets.

    .. warning::

        At this point this only supports input files. Shall we consider extending
        the interface for writing output files as well?

    Arguments
    ---------
    readout_class : type
        The concrete class representing the readout type encoded in the file,
        e.g., ``AstroPix4Readout``.
    """

    _EXTENSION = '.apx'

    def __init__(self, readout_class: type) -> None:
        """Constructor.
        """
        if not issubclass(readout_class, AbstractAstroPixReadout):
            raise RuntimeError(f'{readout_class.__name__} is not a subclass of '
                               'AbstractAstroPixReadout')
        if readout_class is AbstractAstroPixReadout:
            raise RuntimeError('AbstractAstroPixReadout is abstract and should not be instantiated')
        self._readout_class = readout_class
        self.header = None
        self._input_file = None

    @staticmethod
    def read_file_header(file_path: str):
        """Convenience function to retrieve the header of a given astropix binary file.

        Note this is opening and (immediately) closing the file, and can be used
        in the situations where one is only interested into the file header.

        Arguments
        ---------
        file_path : str
            Path to the input astropix binary file.
        """
        with open(file_path, 'rb') as input_file:
            return FileHeader.read(input_file)

    @contextmanager
    def open(self, file_path: str):
        """Open the file.

        Arguments
        ---------
        file_path : str
            Path to the input astropix binary file.
        """
        if not file_path.endswith(self._EXTENSION):
            raise RuntimeError(f'Input file {file_path} has not the {self._EXTENSION} extension')
        logger.info(f'Opening input file {file_path}...')
        with open(file_path, 'rb') as input_file:
            self._input_file = input_file
            self.header = FileHeader.read(self._input_file)
            yield self
            self._input_file = None
        logger.info(f'Input file {file_path} closed.')

    def __iter__(self) -> 'AstroPixBinaryFile':
        """Return the iterator object (self).
        """
        return self

    def __next__(self) -> AbstractAstroPixReadout:
        """Read the next readout in the file.
        """
        readout = self._readout_class.from_file(self._input_file)
        if readout is None:
            raise StopIteration
        return readout

    def to_table(self, col_names: list[str], data_types) -> astropy.table.Table:
        """Convert the file to a astropy table.
        """
        logger.info(f'Converting {self._input_file.name} to an astropy table...')
        table = astropy.table.Table(names=col_names, dtype=data_types)
        for readout in self:
            hits = readout.decode()
            for hit in hits:
                values = (hit.chip_id, hit.row, hit.column, hit.tot_us,
                          hit.readout_id, hit.timestamp)
                table.add_row(values)
        logger.info(f'Done, {len(table)} row(s) populated.')
        return table


def _convert_apx(input_file_path: str, readout_class: type, converter: typing.Callable,
                 extension: str, output_file_path: str = None, header: str = None,
                 open_mode: str = 'w', encoding: str = FileHeader.ENCODING) -> str:
    """Generic conversion factory for AstroPixBinaryFile objects.

    This is designed to open an astropix binary files, loop over the readouts and
    hits inside, and write the data to a (properly formatted output file). This
    method should help implementing actual converters, e.g., to cvs of HDF5 formats.

    Arguments
    ---------
    input_file_path : str
        The path to the input astropix binary file (this should have the .apx extension).

    readout_class : type
        The concrete AbstractAstroPixReadout subclass of the readout object written
        in the input file.

    converter : callable
        The conversion method mapping the hits in the input file to the content
        of the output file. (Note we are calling ``converter(hit)`` in the event
        loop, so this might either be a method of the proper hit class, or anything
        that can operate accepting a hit object as the only argument.)

    extension : str
        Extension for the output file, including the leading ``.`` (e.g, ``.csv``).
        This is used to determine the path to the output file when the latter is
        not passed as an argument.

    output_file_path : str (optional)
        The full path to the output file. If this is None, the path is made by
        just changing the extension of the input file.

    header : str (optional)
        Optional header information, to be written at the beginning of the output
        file.

    open_mode : str (default 'w')
        The open mode for the output file.

    encoding : str (default FileHeader.ENCODING)
        The encoding (when necessary) for the output file.
    """
    # pylint: disable=protected-access
    _ext = AstroPixBinaryFile._EXTENSION
    # Check the extension of the input file.
    if not input_file_path.endswith(_ext):
        raise RuntimeError(f'{input_file_path} has the wrong extension (expecting {_ext})')
    # If we don't provide the full path to the output file, we make up one by just
    # changing the file extension.
    if output_file_path is None and extension is not None:
        output_file_path = input_file_path.replace(_ext, extension)
    if not output_file_path.endswith(extension):
        raise RuntimeError(f'{output_file_path} has the wrong extension (expecting {extension})')
    # We are ready to go.
    logger.info(f'Converting {input_file_path} file to {output_file_path}...')
    # Open the input and output files...
    with AstroPixBinaryFile(readout_class).open(input_file_path) as input_file, \
         open(output_file_path, open_mode, encoding=encoding) as output_file:
        # If necessary, write the header.
        if header is not None:
            output_file.write(header)
        # Start the event loop.
        num_hits = 0
        for readout in input_file:
            for hit in readout.decode():
                output_file.write(converter(hit))
                num_hits += 1
    logger.info(f'Done, {num_hits} hit(s) written')
    return output_file_path


def apx_to_csv(input_file_path: str, readout_class: type, output_file_path: str = None) -> str:
    """Convert an AstroPix binary file to csv.
    """
    hit_class = readout_class.HIT_CLASS
    converter = hit_class.to_csv
    extension = '.csv'
    # We need to decide whether we want to include some representation of the
    # header of the input file in the output cvs file?
    apx_header = AstroPixBinaryFile.read_file_header(input_file_path)
    header = f'# {apx_header}\n# {hit_class.text_header()}\n'
    return _convert_apx(input_file_path, readout_class, converter, extension,
                        output_file_path, header)
