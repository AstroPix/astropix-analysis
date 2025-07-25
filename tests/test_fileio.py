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


"""Unit tests for the fileio.py module.
"""

import os
import tempfile

import numpy as np

from astropix_analysis import logger, ASTROPIX_ANALYSIS_TESTS_DATA
from astropix_analysis.fileio import FileHeader, AstroPixBinaryFile, \
    apx_process, apx_load, SUPPORTED_TABLE_FORMATS
from astropix_analysis.fmt import AstroPix4Readout


# Mock data from a small test run with AstroPix4---the bytearray below should
# be exactly what might come out from a NEXYS board with the AstroPix 4 firmware.
# (For completeness, data were taken on 2024, December 19, and the array if
# taken verbatim from the log file. The readout contains exactly 2 hits.)
# pylint: disable=line-too-long
SAMPLE_READOUT_DATA = bytearray.fromhex('bcbce08056e80da85403bcbcbcbcbcbcbcbce080d26f04ca3005bcbcbcbcbcbcffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff')  # noqa: E501

SAMPLE_RUN_ID = '20250723_092534'


def _rm_tmpfile(file_) -> None:
    """Delete a temporary file.

    Note we resort to manually delete the temporary files because the
    ``delete_on_close`` argument, which would be handy in a context where we
    want to do something with the files, was only introduced in Python 3.12 and
    we are targeting Python 3.7 as the oldest version we tentatively support.
    """
    file_path = file_.name
    logger.debug(f'Removing temporary file {file_path}...')
    os.remove(file_path)


def test_file_header():
    """Test the file header.

    This creates a fictional FileHeader object, writes it to an output file, reads
    it back, and makes sure it is correct.
    """
    # pylint: disable=protected-access
    # Create a dummy header.
    header = FileHeader(AstroPix4Readout, dict(version=1, content='hits'))
    print(header)
    # Write the header to an output file.
    kwargs = dict(suffix=AstroPixBinaryFile._EXTENSION, delete=False)
    with tempfile.NamedTemporaryFile('wb', **kwargs) as output_file:
        print(f'Writing header to {output_file.name}...')
        header.write(output_file)
        output_file.close()
    # Read back the header from the output file.
    print(f'Reading header from {output_file.name}...')
    with open(output_file.name, 'rb') as input_file:
        twin = FileHeader.read(input_file)
    print(twin)
    # Make sure that the whole thing roundtrips.
    assert twin == header
    # Remove the temporary file.
    _rm_tmpfile(output_file)


def test_file_write_read():
    """Try writing and reading a fully-fledged output file.
    """
    # pylint: disable=protected-access
    # Create a dummy header.
    header = FileHeader(AstroPix4Readout, dict(version=1, content='hits'))
    print(header)
    # Grab our test AstroPix4 hits.
    readout = AstroPix4Readout(SAMPLE_READOUT_DATA, 0)
    hits = readout.decode()
    # Write the output file.
    kwargs = dict(suffix=AstroPixBinaryFile._EXTENSION, delete=False)
    with tempfile.NamedTemporaryFile('wb', **kwargs) as output_file:
        print(f'Writing data to {output_file.name}...')
        header.write(output_file)
        readout.write(output_file)
        output_file.close()
    # Read back the input file---note this is done in the context of the first
    # with, so that tempfile can cleanup after the fact.
    print(f'Reading data from {output_file.name}...')
    with AstroPixBinaryFile().open(output_file.name) as input_file:
        print(input_file.header)
        _readout = next(input_file)
        _hits = _readout.decode()
        for i, _hit in enumerate(_hits):
            print(_hit)
            assert _hit == hits[i]
    # Remove the temporary file.
    _rm_tmpfile(output_file)


def test_playback_data(num_hits: int = 10):
    """Test the full playback of a real file.

    This is just playing back the entire file, and prints out the first few readouts
    and associated hits.
    """
    file_path = ASTROPIX_ANALYSIS_TESTS_DATA / SAMPLE_RUN_ID / f'{SAMPLE_RUN_ID}_data.apx'
    # We should support pathlib upstream.
    file_path = str(file_path)
    with AstroPixBinaryFile().open(file_path) as input_file:
        print(f'\nStarting playback of binary file {file_path}...')
        print(f'File header: {input_file.header}')
        i = 0
        for i, readout in enumerate(input_file):
            hits = readout.decode()
            if i < num_hits:
                print(readout)
                for hit in hits:
                    print(f'-> {hit}')
            elif i == num_hits:
                print('...')
        print(f'{i + 1} hits found')


def test_table():
    """Test the table conversion.
    """
    file_path = ASTROPIX_ANALYSIS_TESTS_DATA / SAMPLE_RUN_ID / f'{SAMPLE_RUN_ID}_data.apx'
    # We should support pathlib upstream.
    file_path = str(file_path)
    col_names = ('chip_id', 'row', 'column', 'tot_us', 'readout_id', 'timestamp')
    with AstroPixBinaryFile().open(file_path) as input_file:
        table = input_file.to_table(col_names)
    print(table)


def test_table_io():
    """Test the full IO from the binary astropix format to all the supported
    analysis formats.
    """
    file_path = ASTROPIX_ANALYSIS_TESTS_DATA / SAMPLE_RUN_ID / f'{SAMPLE_RUN_ID}_data.apx'
    # We should support pathlib upstream.
    file_path = str(file_path)

    # Loop over the input file once and create an astropy table in memory.
    with AstroPixBinaryFile().open(file_path) as input_file:
        original_table = input_file.to_table()
    num_cols = len(original_table.columns)
    num_rows = len(original_table)

    # Make sure that, for all the supported format, the I/O roundtrips
    for format_ in SUPPORTED_TABLE_FORMATS:
        # Convert the binary file to a given data format...
        kwargs = dict(suffix=f'.{format_}', delete=False)
        with tempfile.NamedTemporaryFile('w', **kwargs) as output_file:
            output_file.close()
            args = file_path, format_, None, output_file.name
            assert apx_process(*args) == output_file.name
        # ... read back the table...
        header, table = apx_load(output_file.name)
        print(header)
        print(header['configuration'])
        print(table)
        # And make sure it looks identical to the original one.
        assert len(table.columns) == num_cols
        assert len(table) == num_rows
        for col_name in table.colnames:
            logger.debug(f'Checking column {col_name} against the original file...')
            assert np.allclose(table[col_name], original_table[col_name])
        # Remove the temporary file.
        _rm_tmpfile(output_file)
