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


class LogFileHeader:

    """Convenience class to interact with the metadata at the top of a log file.

    The class constructor will read just enough lines from the input file to populate
    the header content, and leave the file itself at the first line containing a
    readout. If an actual readout is instead encountered in the process (e.g., when
    the header information is missing, or incomplete), a ``RuntimeError`` is raised.

    Arguments
    ---------
    input_file : TextIO
        The input (text) file object, open in read mode.
    """

    def __init__(self, input_file: typing.TextIO) -> None:
        """Constructor.
        """
        self.voltage_card = self._parse_line(input_file)
        self.digital = self._parse_line(input_file)
        self.bias_block = self._parse_line(input_file)
        self.idac = self._parse_line(input_file)
        self.vdac = self._parse_line(input_file)
        self.receiver = self._parse_line(input_file)
        self.options = self._parse_line(input_file, False)

    @staticmethod
    def _parse_line(input_file: typing.TextIO, split_line: bool = True):
        """Parse one single line from a log file.

        We have to cases here, which are handled differently:

        1. the line contains info from the underlying yaml file, e.g.
          ``Voltagecard: {'thpmos': 0, 'cardConf2': 0,...``
          and we have to split for a column and eval the second part;
        2. the line contains the command-line options in the for of a namespace, e.g.,
          ``Namespace(name='threshold_40mV',..``
          in which case we have nothing to do.

        Arguments
        ---------
        input_file : TextIO
            The input (text) file object, open in read mode.

        split_line : bool
            Indicates whether the input line should be split.
        """
        # pylint: disable=eval-used
        pos = input_file.tell()
        line = input_file.readline()
        if line[0].isdigit():
            input_file.seek(pos)
            raise RuntimeError('Could not parse log file header')
        if split_line:
            _, line = line.split(':', 1)
        return eval(line)

    def inject_pixels(self) -> bool:
        """Return whether the charge injection was enabled.
        """
        return self.options.inject

    def trigger_threshold(self) -> float:
        """Return the trigger threshold.
        """
        return self.options.threshold

    def running_time(self) -> float:
        """ Running time in seconds
        """
        return self.options.maxtime * 60

    def injection_voltage(self) -> float:
        """Return the injection voltage.
        """
        return self.options.vinj

    def __str__(self) -> str:
        """String formatting.
        """
        return f'{self.__class__.__name__}'\
               f"({', '.join(f'{key} = {value}' for key, value in self.__dict__.items())})"


class AstroPixLogFile:

    """Minimal, read-only interface to legacy astropix .log files.
    """

    EXTENSION = '.log'

    def __init__(self, file_path: str) -> None:
        """Constructor.
        """
        file_path = sanitize_path(file_path, self.EXTENSION)
        self._file_path = file_path
        self._file = None
        self.header = None
        self._readout_class = None

    def __enter__(self):
        """Context manager protocol implementation.
        """
        # pylint: disable=unspecified-encoding
        logger.debug(f'Opening file {self._file_path}...')
        self._file = open(self._file_path, 'r')
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
    header = FileHeader(readout_class)
    with AstroPixLogFile(input_file_path) as input_file, \
            apx_open(output_file_path, 'wb', header) as output_file:
        num_readouts = 0
        for readout_id, readout_data in input_file:
            readout_data = bytes.fromhex(readout_data)
            readout = AstroPix4Readout(readout_data, readout_id, timestamp=0)
            readout.write(output_file)
            num_readouts += 1
    if num_readouts == 0:
        logger.warning('Input file appears to be empty.')
        return output_file_path
    logger.info(f'All done, {num_readouts} readout(s) written to {output_file_path}')
    return output_file
