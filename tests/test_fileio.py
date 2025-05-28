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
import time

import matplotlib.pyplot as plt
import numpy as np

from astropix_analysis import logger
from astropix_analysis.fileio import FileHeader, AstroPixBinaryFile, apxdf_to_csv
from astropix_analysis.fmt import AstroPix4Readout, AstroPix4Hit
from astropix_analysis.plt_ import plt


# Mock data from a small test run with AstroPix4---the bytearray below should
# be exactly what might come out from a NEXYS board with the AstroPix 4 firmware.
# (For completeness, data were taken on 2024, December 19, and the array if
# taken verbatim from the log file. The readout contains exactly 2 hits.)
SAMPLE_READOUT_DATA = bytearray.fromhex('bcbce08056e80da85403bcbcbcbcbcbcbcbce080d26f04ca3005bcbcbcbcbcbcffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff')


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
    # Create a dummy header.
    header = FileHeader(dict(version=1, content='hits'))
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
    # Create a dummy header.
    header = FileHeader(dict(version=1, content='hits'))
    print(header)
    # Grab our test AstroPix4 hits.
    readout_id = 0
    timestamp=time.time_ns()
    readout = AstroPix4Readout(SAMPLE_READOUT_DATA, readout_id, timestamp)
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
    with AstroPixBinaryFile(AstroPix4Hit).open(output_file.name) as input_file:
        print(input_file.header)
        _readout = next(input_file)
        _hits = readout.decode()
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
    run_id = '20250507_085829'
    file_name = f'{run_id}_data.apx'
    file_path = os.path.join(os.path.dirname(__file__), 'data', run_id, file_name)
    with AstroPixBinaryFile(AstroPix4Hit).open(file_path) as input_file:
        print(f'\nStarting playback of binary file {file_path}...')
        print(f'File header: {input_file.header}')
        for i, readout in enumerate(input_file):
            hits = readout.decode()
            if i < num_hits:
                print(readout)
                for hit in hits:
                    print(f'-> {hit}')
            elif i == num_hits:
                print('...')
        print(f'{i + 1} hits found')


def test_csv_convert():
    """Read a sample real .apx file and convert it to csv.

    Note we don't really do much with the converted file, other than printing a
    few lines on the terminal---we do verify, though, that the conversion get to
    the end of the input file.
    """
    run_id = '20250507_085829'
    file_name = f'{run_id}_data.apx'
    file_path = os.path.join(os.path.dirname(__file__), 'data', run_id, file_name)
    kwargs = dict(suffix='.csv', delete=True)
    with tempfile.NamedTemporaryFile('w', **kwargs) as output_file:
        # Horrible trick to get a path to a temp file, rather than an actual file object.
        output_file.close()
        out = apxdf_to_csv(file_path, AstroPix4Hit, output_file_path=output_file.name)
        assert out == output_file.name
        with open(output_file.name) as _out:
            for _ in range(10):
                print(_out.readline())
    # Remove the temporary file.
    _rm_tmpfile(output_file)


# def test_plot_file():
#     """Basic test plotting the content of the sample binary file.

#     FIXME: move to test_analysis.
#     """
#     run_id = '20250507_085829'
#     file_name = f'{run_id}_data.csv'
#     file_path = os.path.join(os.path.dirname(__file__), 'data', run_id, file_name)
#     chip_id, payload, row, column, ts_neg1, ts_coarse1, ts_fine1, ts_tdc1, ts_neg2, \
#         ts_coarse2, ts_fine2, ts_tdc2, ts_dec1, ts_dec2, tot_us, readout_id, timestamp = \
#         np.loadtxt(file_path, delimiter=',', unpack=True)
#     dt = np.diff(timestamp) / 1.e6

#     plt.figure('TOT')
#     plt.hist(tot_us, bins=25)
#     plt.xlabel('TOT [$\\mu$s]')

#     plt.figure('Time differences')
#     plt.hist(dt, bins=25)
#     plt.xlabel('$\\Delta$T [ms]')
