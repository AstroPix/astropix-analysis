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

"""Facilities for legacy .log data files.
"""

# pylint: disable=unused-import
from argparse import Namespace  # noqa: F401
import typing

from astropix_analysis import logger
from astropix_analysis.fileio import apx_open, FileHeader, sanitize_path
from astropix_analysis.fmt import AstroPix4Readout


class LogFileHeader(dict):

    """Convenience class to interact with the metadata at the top of a log file.

    The class constructor will read just enough lines from the input file to populate
    the header content, and leave the file itself at the first line containing a
    readout. If an actual readout is instead encountered in the process (e.g., when
    the header information is missing, or incomplete), a ``RuntimeError`` is raised.

    Note this class respect the contract that we have for the actual header of
    .apx file, i.e., it is a dictionary containing simple Python types that can
    be seamlessly serialized and deserialized. (This is necessary if we want to
    convert .log files into .apx files preserving the metadata.)

    Note the typical structure of the file is

    .. code-block::

        Voltagecard: {'thpmos': 0, 'cardConf2': 0, 'vcasc2': 1.1, 'BL': 1, ...
        Digital: {'interrupt_pushpull': 0, 'clkmux': 0, 'timerend': 0, ...
        Biasblock: {'DisHiDR': 0, 'q01': 0, 'qon0': 0, 'qon1': 1, 'qon2': 0, ...
        iDAC: {'blres': 0, 'vpdac': 10, 'vn1': 20, 'vnfb': 1, 'vnfoll': 2, ...
        vDAC: {'blpix': 568, 'thpix': 610, 'vcasc2': 625, 'vtest': 682, ...
        Receiver: {'col0': 206158430206, 'col1': 68719476735, 'col2': 68719476734, ...
         Namespace(name='threshold_40mV',...
        0	b'bcbce050fecd067cc500bcbcbcbcbcbcfffffffffffffffffffffffffffffffffffffffff

    Arguments
    ---------
    input_file : TextIO
        The input (text) file object, open in read mode.
    """

    _OPTIONS_KEY = 'options'

    def __init__(self, input_file: typing.TextIO) -> None:
        """Constructor.
        """
        # pylint: disable=eval-used
        # Call the dict constructor.
        super().__init__()
        logger.debug('Parsing .log file metadata...')
        line = None
        # Loop over the lines in the input file...
        while line != '':
            # Note we need to keep track of the position within the file because,
            # as soon as we find a line with readout data, we want to roll back by
            # one line.
            pos = input_file.tell()
            line = input_file.readline()
            # If we encouter an empty line, this probably means that we have read all
            # the metadata, and the file does not contain readout data.
            if line == '':
                logger.warning(f'{input_file.name} does not seem to contain readout data!')
                return
            # If the first character of the line is a digit, we roll back to the
            # previous line and return.
            if line[0].isdigit():
                input_file.seek(pos)
                return
            # Parse the line and cache the data. Note the asymmetry between the
            # two kinds of metadata:
            line = line.strip('\n')
            if ': {' in line:
                # 1. Stuff from the underlying yaml file...
                key, data = line.split(':', 1)
                self[key] = eval(data)
            else:
                # 2. ...and final argparse.Namespace with the command-line options.
                self[self._OPTIONS_KEY] = vars(eval(line))

    def options(self) -> dict:
        """Return the dictionary with the command-line options.
        """
        return self[self._OPTIONS_KEY]

    def __str__(self) -> str:
        """String formatting.
        """
        return f'{self.__class__.__name__}'\
               f"({', '.join(f'{key} = {value}' for key, value in self.items())})"


class AstroPixLogFile:

    """Minimal, read-only interface to legacy astropix .log files.
    """

    EXTENSION = '.log'

    def __init__(self, file_path: str, encoding: str = 'utf-8') -> None:
        """Constructor.
        """
        file_path = sanitize_path(file_path, self.EXTENSION)
        self._file_path = file_path
        self._encoding = encoding
        self._file = None
        self.header = None

    def __enter__(self) -> 'AstroPixLogFile':
        """Context manager protocol implementation.
        """
        logger.debug(f'Opening file {self._file_path}...')
        self._file = open(self._file_path, 'r', encoding=self._encoding)
        self.header = LogFileHeader(self._file)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager protocol implementation.
        """
        # pylint: disable=duplicate-code
        if self._file:
            logger.debug(f'Closing file {self._file_path}...')
            self._file.close()

    def __iter__(self) -> 'AstroPixLogFile':
        """Return the iterator object (self).
        """
        return self

    def __next__(self) -> typing.Tuple[int, str]:
        """Read the next readout in the file and return a a 2-element tuple
        containing the readout ID and the actual readout data in text form.
        """
        line = self._file.readline()
        if line == '':
            raise StopIteration
        readout_id, readout_data = line.strip('\n').split('\t')
        readout_id = int(readout_id)
        readout_data = readout_data.replace('b\'', '').replace('\'', '')
        return readout_id, readout_data


def log_to_apx(input_file_path: str, readout_class: type = AstroPix4Readout,
               output_file_path: str = None) -> str:
    """Convert a .log (text) file to a .apx (binary) file.
    """
    input_file_path = sanitize_path(input_file_path, AstroPixLogFile.EXTENSION)
    if output_file_path is None:
        output_file_path = input_file_path.replace('.log', '.apx')
    logger.info(f'Converting input file {input_file_path} to {output_file_path}')
    with AstroPixLogFile(input_file_path) as input_file:
        if len(input_file.header) == 0:
            logger.warning('No metadata found in the input .log file!')
        header = FileHeader(readout_class, input_file.header)
        logger.debug(header)
        with apx_open(output_file_path, 'wb', header) as output_file:
            num_readouts = 0
            for readout_id, readout_data in input_file:
                # Interesting: when analyzing the high-rate strontium data taken
                # at GSFC we found that, while typically readouts are 4096 bytes
                # long, there is a few instances where the last byte is apparently
                # missing, and the the ``bytes.fromhex`` call fails. For the
                # time being I am logging out some debug information and skipping
                # the readout, but I also opened
                # https://github.com/AstroPix/astropix-analysis/issues/15
                # in order not to forget this.
                try:
                    readout_data = bytes.fromhex(readout_data)
                except ValueError as exception:
                    logger.warning(f'{exception} for readout {readout_id}')
                    continue
                readout = AstroPix4Readout(readout_data, readout_id, timestamp=0)
                readout.write(output_file)
                num_readouts += 1
    if num_readouts == 0:
        logger.warning('Input file appears to be empty.')
        return output_file_path
    logger.info(f'All done, {num_readouts} readout(s) written to {output_file_path}')
    return output_file
