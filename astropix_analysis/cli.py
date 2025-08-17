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

"""Command-line arguments.
"""


import argparse
import os
import pathlib

from astropix_analysis import logger, LOGGING_LEVELS, DEFAULT_LOGGING_LEVEL, \
    reset_logger, start_message
from astropix_analysis import sock


class _Formatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):

    """Do nothing class combining our favorite formatting for the
    command-line options, i.e., the newlines in the descriptions are
    preserved and, at the same time, the argument defaults are printed
    out when the --help options is passed.

    The inspiration for this is coming from one of the comments in
    https://stackoverflow.com/questions/3853722
    """


class ArgumentParser(argparse.ArgumentParser):

    """Application-wide argument parser.
    """

    def __init__(self, description: str, epilog: str = None) -> None:
        """Constructor.
        """
        super().__init__(description=description, epilog=epilog, formatter_class=_Formatter)
        self.add_loglevel()

    @staticmethod
    def _expand_wildcards(file_list: list) -> list:
        """Expand the wildcards in a given list of file paths.

        This is intended to emulate the bash shell expansion under Windows
        when the ``infiles`` command-line argument is passed.

        See https://github.com/AstroPix/astropix-analysis/issues/16
        """
        # Make sure the input argument is a list---this is what we are expecting
        # from args.infiles and this is a horrible hack specific for that.
        if not isinstance(file_list, list):
            raise RuntimeError(f'{file_list} is not a list')
        expanded_list = []
        for file_path in file_list:
            if '*' not in file_path:
                expanded_list += [file_path]
            else:
                logger.debug(f'Expanding wildcards in {file_path}...')
                parent, pattern = file_path.split('*', 1)
                pattern = f'*{pattern}'
                partial_list = [str(_path) for _path in pathlib.Path(parent).glob(pattern)]
                logger.debug(f'{len(partial_list)} file(s) found.')
                expanded_list += partial_list
        return expanded_list

    def parse_args(self, args: list = None,
                   namespace: argparse.Namespace = None) -> argparse.Namespace:
        """Overloaded method.

        This is calling the method from the base class and, before returning the
        arguments, resets the logger with the proper level---so that this operation
        happens transparently for the user with no boilerplate code.
        """
        # First thing first, print the start message.
        print(start_message())
        # Parse the arguments
        args = super().parse_args()
        # Setup the logger.
        reset_logger(args.loglevel)
        # If we are under Windows we try and expand the wildcards.
        if os.name == 'nt' and 'infiles' in args:
            args.infiles = self._expand_wildcards(args.infiles)
        # And we are good to go!
        return args

    def add_infile(self) -> None:
        """Add the ``infile`` argument.
        """
        self.add_argument('infile', type=str,
                          help='path to the input file')

    def add_infiles(self) -> None:
        """Add the ``infiles`` argument.
        """
        self.add_argument('infiles', type=str, nargs='+',
                          help='path to the input file(s)')

    def add_loglevel(self) -> None:
        """Add the ``loglevel`` argument.
        """
        self.add_argument('--loglevel', type=str, choices=LOGGING_LEVELS,
                          default=DEFAULT_LOGGING_LEVEL,
                          help='logging level')

    def add_multicast(self) -> None:
        """Add all the relevant multicast options.
        """
        group = self.add_argument_group('multicast options')
        group.add_argument('--group', type=str, default=sock.LOCAL_HOST,
                           help='multicast group')
        group.add_argument('--port', type=int, default=sock.DEFAULT_PORT,
                           help='multicast port')

    def add_refresh(self, default: float) -> None:
        """Add the refresh argument (interval in s).
        """
        self.add_argument('--refresh', type=float, default=default,
                          help='refresh interval in seconds')

    def add_start(self) -> None:
        """Add the ``start`` argument.
        """
        self.add_argument('--start', type=int, default=0,
                          help='start from a given readout id')
