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

from astropix_analysis import LOGGING_LEVELS, DEFAULT_LOGGING_LEVEL, reset_logger


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

    def parse_args(self, args: list = None,
                   namespace: argparse.Namespace = None) -> argparse.Namespace:
        """Overloaded method.

        This is calling the method from the base class and, before returning the
        arguments, resets the logger with the proper level---so that this operation
        happens transparently for the user with no boilerplate code.
        """
        args = super().parse_args()
        reset_logger(args.loglevel)
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

    def add_start(self) -> None:
        """Add the ``start`` argument.
        """
        self.add_argument('--start', type=int, default=0,
                          help='start from a given readout id')
