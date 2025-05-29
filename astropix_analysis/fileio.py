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

from astropix_analysis import logger
from astropix_analysis.fmt import AstroPix4Hit, AstroPix4Readout


class FileHeader:

    """Class describing a file header.

    The content of the header can be literally anything that is json-serializable,
    i.e., the only request that we make is that ``json.dumps(self._content)``
    is not raising an exception.

    The basic contract is that when the ``write()`` method is called we write
    into the output binary file:

    * the header magic word (``%APXDF`` for AstroPix Data Format);
    * the length of the header content in bytes;
    * the actual header content.

    In the opposite direction, when the ``read()`` hook is called, we do:

    * read the first small chunk of the binary file and make sure the magic word is correct;
    * read the header length;
    * read and deserialize the header conten, returning a full fledges ``FileHeader`` object.

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
            raise RuntimeError(f'Invalid magic word ({magic}), expected {cls.MAGIC_NUMBER}')
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
    hit_class : type
        The class representing the hit type encoded in the file, e.g., ``AstroPix4Hit``.
    """

    _EXTENSION = '.apx'

    def __init__(self, hit_class: type) -> None:
        """Constructor.
        """
        self._hit_class = hit_class
        self.header = None
        self._input_file = None

    @contextmanager
    def open(self, file_path: str):
        """Open the file.

        Arguments
        ---------
        file_path : str
            Path to the file to be read.
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

    def __next__(self) -> AstroPix4Readout:
        """Read the next packet in the buffer.
        """
        readout = AstroPix4Readout.from_file(self._input_file)
        if readout is None:
            raise StopIteration
        return readout


def _convert_apxdf(file_path: str, hit_class: type, converter: typing.Callable,
                   header: str = None, output_file_path: str = None, open_mode: str = 'w',
                   default_extension: str = None) -> str:
    """Generic conversion factory for AstroPixBinaryFile objects.
    """
    if output_file_path is None and default_extension is not None:
        output_file_path = file_path.replace('.apx', default_extension)
    logger.info(f'Converting {file_path} file to {output_file_path}...')
    with AstroPixBinaryFile(hit_class).open(file_path) as input_file, \
         open(output_file_path, open_mode) as output_file:
        if header is not None:
            output_file.write(header)
        num_hits = 0
        for readout in input_file:
            for hit in readout.decode():
                output_file.write(converter(hit))
                num_hits += 1
    logger.info(f'Done, {num_hits} hit(s) written')
    return output_file_path


def apxdf_to_csv(file_path: str, hit_class: type = AstroPix4Hit,
                 output_file_path: str = None) -> str:
    """Convert an AstroPix binary file to csv.
    """
    header = f'# {AstroPix4Hit.text_header()}\n'
    return _convert_apxdf(file_path, hit_class, hit_class.to_csv, header,
                          output_file_path, 'w', '.csv')
