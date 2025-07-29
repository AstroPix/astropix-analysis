#!/usr/bin/env python3
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

"""Processing script for astropix binary files.
"""

import argparse

from astropix_analysis.cli import ArgumentParser
from astropix_analysis.fileio import SUPPORTED_TABLE_FORMATS, apx_process


_DESCRIPTION = f"""Astropix binary data file processing.

This allows to extract the hits in a generic binary file and save them in a
number of formats {SUPPORTED_TABLE_FORMATS}.
"""


def main(args: argparse.Namespace) -> None:
    """Actual conversion function.
    """
    for file_path in args.infiles:
        apx_process(file_path, args.format, args.columns)


if __name__ == "__main__":

    parser = ArgumentParser(description=_DESCRIPTION)
    parser.add_infiles()
    parser.add_argument('--format', type=str, choices=SUPPORTED_TABLE_FORMATS,
                        required=True,
                        help='output data format')
    parser.add_argument('--columns', nargs='+', type=str, default=None,
                        help='columns selected for the output file')
    main(parser.parse_args())
