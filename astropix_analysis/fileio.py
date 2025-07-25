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

import json
import pathlib
import struct
import time
import typing

import astropy.table

from astropix_analysis import logger
from astropix_analysis.fmt import AbstractAstroPixReadout, uid_to_readout_class, AstroPix4Readout


class FileHeader:

    """Class describing a file header.

    The content of the header is assumed to be a dict object that is json-serializable,
    i.e., the main request that we make is that ``json.dumps(self._content)``
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
    readout_class : type
        The readout class for the event data in the file.

    content : anything that is serializable
        The header content.
    """

    MAGIC_NUMBER = '%APXDF'
    _HEADER_LENGTH_FMT = '<I'
    _READOUT_UID_KEY = 'readout_uid'
    ENCODING = 'utf-8'

    def __init__(self, readout_class: type, content: dict = None) -> None:
        """Constructor.

        Note that the `readout_uid` is mandatory, while any other additional data
        to be included in the header is optional, and should take the form of a
        dictionary. Internally, the two things are merged together into a single
        dict object.
        """
        self._content = {self._READOUT_UID_KEY: readout_class.uid()}
        if content is not None:
            self._content.update(content)

    def readout_uid(self) -> int:
        """Return the unique ID for the readout class of the data in the file.
        """
        return self._content[self._READOUT_UID_KEY]

    def readout_class(self) -> type:
        """Return the actual class for the readout data in the file.
        """
        return uid_to_readout_class(self.readout_uid())

    def serialize(self) -> str:
        """Serialize the header into a piece of text.
        """
        return json.dumps(self._content)

    @classmethod
    def deserialize(cls, text: str) -> FileHeader:
        """Deserialize a fully-fledged FileHeader object from a piece of text.
        """
        # This is less than trivial, as in the actual file the readout_uid is
        # flattened into a single dict object, along with all the other data,
        # and, in order to rebuild the header object, we need to pop out the
        # uid and pass it to the class constructor as a distinct object.
        data = json.loads(text)
        readout_uid = data.pop('readout_uid')
        return cls(uid_to_readout_class(readout_uid), data)

    def __getitem__(self, item):
        """Make the header indexable.
        """
        return self._content[item]

    def write(self, output_file: typing.BinaryIO) -> None:
        """Serialize the header structure to an output binary file.

        Arguments
        ---------
        output_file : BinaryIO
            A file object opened in "wb" mode.
        """
        data = self.serialize().encode(self.ENCODING)
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
        text = input_file.read(header_length).decode(cls.ENCODING)
        return cls.deserialize(text)

    def __eq__(self, other: 'FileHeader') -> bool:
        """Comparison operator---this is useful in the unit tests in order to make
        sure that the serialization/deserialization roundtrips.
        """
        return self.readout_uid() == other.readout_uid() and self._content == other._content

    def __str__(self) -> str:
        """String representation.
        """
        fields = ', '.join(f'{key}={value}' for key, value in self._content.items())
        return f'Header({fields})'


class AstroPixBinaryFile:

    """Class describing a .apx file.
    """

    _EXTENSION = '.apx'
    _VALID_OPEN_MODES = ('rb', 'wb')

    def __init__(self, file_path: str, mode: str = 'rb', header: FileHeader = None) -> None:
        """Constructor.
        """
        if isinstance(file_path, pathlib.Path):
            file_path = f'{file_path}'
        if not file_path.endswith(self._EXTENSION):
            raise RuntimeError(f'Input file {file_path} has not the {self._EXTENSION} extension')
        if mode not in self._VALID_OPEN_MODES:
            raise ValueError(f'Invalid open mode ({mode}) for {self.__class__.__name__}')
        if mode == 'wb' and header is None:
            raise RuntimeError(f'Cannot open {file_path} file in write mode without a header')
        self._file_path = file_path
        self._mode = mode
        self._file = None
        self.header = header
        self._readout_class = None

    def __enter__(self):
        """Context manager protocol implementation.
        """
        # pylint: disable=unspecified-encoding
        logger.debug(f'Opening file {self._file_path}...')
        self._file = open(self._file_path, self._mode)
        if self._mode == 'rb':
            self.header = FileHeader.read(self._file)
            self._readout_class = self.header.readout_class()
        elif self._mode == 'wb':
            self.header.write(self._file)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager protocol implementation.
        """
        if self._file:
            logger.debug(f'Closing file {self._file_path}...')
            self._file.close()

    def __iter__(self) -> 'AstroPixBinaryFile':
        """Return the iterator object (self).
        """
        return self

    def __next__(self) -> AbstractAstroPixReadout:
        """Read the next readout in the file.
        """
        if self._mode != 'rb':
            raise IOError('File not open for reading')
        readout = self._readout_class.from_file(self._file)
        if readout is None:
            raise StopIteration
        return readout

    def write(self, data):
        """Write data to file.
        """
        if self._mode != 'wb':
            raise IOError('File not open for writing')
        return self._file.write(data)

    def to_table(self, col_names: list[str] = None) -> astropy.table.Table:
        """Convert the file to a astropy table.
        """
        logger.info(f'Converting {self._file.name} to an astropy table...')
        table = self._readout_class.HIT_CLASS.empty_table(col_names)
        for readout in self:
            hits = readout.decode()
            for hit in hits:
                table.add_row(hit.attribute_values(col_names))
        logger.info(f'Done, {len(table)} row(s) populated.')
        logger.info('Adding metadata...')
        # The comments are defined as a list of strings in the input table meta['comments']
        # Note that astropy treats this in a special fashion and, depending on the
        # specific settings, meta['comments'] gets written in the output file
        # in pretty much all formats, so we try and take advantage of this not
        # to loose the header information.
        table.meta['comments'] = [self.header.serialize()]
        return table


def apx_open(file_path: str, mode: str = 'rb', header: FileHeader = None):
    """Main interface for opening .apx files.
    """
    return AstroPixBinaryFile(file_path, mode, header)


# Output data formats that we support, leveraging the astropy.table functionality
#
SUPPORTED_TABLE_FORMATS = ('csv', 'ecsv', 'fits', 'hdf5')

# Keyword arguments passed to the table writers in order to customize the behavior.
# The astropy documentation is not really extensive, here, but you do get some
# useful information from the interactive help, e.g.
# >>> from astropy.table import Table
# >>> Table.write.help('csv')
# >>> Table.read.help('csv')
#
_CSV_COMMENT = '#'
_EXT_NAME = 'HITS'
_TABLE_WRITE_KWARGS = {
    'csv': dict(comment=_CSV_COMMENT),
    'hdf5': dict(path=_EXT_NAME)
}
_TABLE_READ_KWARGS = {
    'csv': dict(comment=_CSV_COMMENT)
}


def apx_process(input_file_path: str, format_: str, col_names: list[str] = None,
                output_file_path: str = None, overwrite: bool = True, **kwargs):
    """Generic binary file conversion function.

    Arguments
    ---------
    input_file_path : str
        The path to the input astropix binary file (this should have the .apx extension).

    format_ : str
        The output format. See https://docs.astropy.org/en/latest/io/unified_table.html
        for a full list of all available options.

    col_names : list of str (optional)
        Hit attributes selected for being included in the output file. By default
        all the attributes are included.

    output_file_path : str (optional)
        The full path to the output file. If this is None, the path is made by
        just changing the extension of the input file.
    """
    # pylint: disable=protected-access
    if isinstance(input_file_path, pathlib.Path):
        input_file_path = f'{input_file_path}'
    # Check the input file extension.
    src_ext = AstroPixBinaryFile._EXTENSION
    if not input_file_path.endswith(src_ext):
        raise RuntimeError(f'{input_file_path} has the wrong extension (expecting {src_ext})')
    # Check the output format
    if format_ not in SUPPORTED_TABLE_FORMATS:
        raise RuntimeError(f'Unsupported tabular format {format_}. '
                           f'Valid formats are {SUPPORTED_TABLE_FORMATS}')
    dest_ext = f'.{format_}'
    # If we don't provide the full path to the output file, we make up one by just
    # changing the file extension.
    if output_file_path is None:
        output_file_path = input_file_path.replace(src_ext, dest_ext)
    # We are ready to go.
    logger.info(f'Processing file {input_file_path}...')
    start_time = time.time()
    with apx_open(input_file_path) as input_file:
        table = input_file.to_table(col_names)
    elapsed_time = time.time() - start_time
    num_hits = len(table)
    rate = num_hits / elapsed_time
    logger.debug(f'{num_hits} hits processed in {elapsed_time:.3f} s ({rate:.1f} hits/s)')
    logger.info(f'Writing tabular data in {format_} format to {output_file_path}...')
    kwargs = _TABLE_WRITE_KWARGS.get(format_, {})
    table.write(output_file_path, overwrite=overwrite, **kwargs)
    return output_file_path


def apx_load(file_path: str) -> astropy.table.Table:
    """Load an astropy table from a given file path.
    """
    logger.info(f'Reading tabular data from {file_path}...')
    format_ = file_path.split('.')[-1]
    kwargs = _TABLE_READ_KWARGS.get(format_, {})
    table = astropy.table.Table.read(file_path, **kwargs)
    # Note we have to join the pieces because the FITS format treats things
    # differently.
    header = FileHeader.deserialize(''.join(table.meta['comments']))
    return header, table


def log_to_apx(input_file_path: str, readout_class: type = AstroPix4Readout,
               output_file_path: str = None, encoding: str = 'utf-8') -> str:
    """Convert a .log (text) file to a .apx (binary) file.
    """
    if not input_file_path.endswith('.log'):
        raise RuntimeError(f'{input_file_path} is not a log file')
    if output_file_path is None:
        output_file_path = input_file_path.replace('.log', '.apx')
    logger.info(f'Converting input file {input_file_path} to {output_file_path}')
    with open(input_file_path, 'r', encoding=encoding) as input_file, \
         open(output_file_path, 'wb') as output_file:
        header = FileHeader(readout_class)
        header.write(output_file)
        is_data = False
        num_readouts = 0
        for line in input_file:
            if line.startswith('0\t'):
                is_data = True
            if is_data:
                readout_id, readout_data = line.split('\t')
                readout_id = int(readout_id)
                readout_data = readout_data.replace('b\'', '').replace('\'\n', '')
                readout_data = bytes.fromhex(readout_data)
                readout = AstroPix4Readout(readout_data, readout_id, timestamp=0)
                readout.write(output_file)
                num_readouts += 1
    if num_readouts == 0:
        logger.warning('Input file appears to be empty.')
        return output_file_path
    logger.info(f'All done, {num_readouts} readout(s) written to {output_file_path}')
    return output_file
