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

from astropix_analysis import logger
from astropix_analysis.fileio import sanitize_path
from astropix_analysis.fmt import AbstractAstroPixReadout


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
        # self.header = FileHeader.read(self._file)
        # self._readout_class = self.header.readout_class()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
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

    def __next__(self) -> AbstractAstroPixReadout:
        """Read the next readout in the file.
        """
        readout = self._readout_class.from_file(self._file)
        if readout is None:
            raise StopIteration
        return readout
